# -*- coding: utf-8 -*-
"""
Akış:  topla → ayrıştır → temizle → kimlik ver → test (hızlı → ilerleme → derin)
       → puanla → kanal başına kaynakları sırala → koruma kontrolü → yaz → raporla
"""
import logging
import os
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutTimeout
from dataclasses import dataclass, field

from . import clean, extra_sources, guard, identity, liveness, official, output, parse, siblings, sources
from . import site_providers
from . import budget
from . import config as C
from .fetch import get_json, get_text
from .health import SourceState, UrlState, geo_grace

log = logging.getLogger("build")


@dataclass
class RunOptions:
    search: bool = True          # GitHub araması
    fetch_sources: bool = True   # kaynak listelerini indir (False = yalnızca hafıza + mevcut liste)
    fetch_sites: bool = True     # siteye özel spor çözücülerini çalıştır
    deep: bool = C.DEEP_PROBE
    progress: bool = C.PROGRESS_CHECK
    max_test: int = C.MAX_TEST
    dry_run: bool = False        # hiçbir şey yazma (deneme)
    state_only: bool = False     # yalnızca hafızayı güncelle, liste yayınlama (Türkiye doğrulaması)


@dataclass
class RunStats:
    t0: float = field(default_factory=time.time)
    sources_total: int = 0
    sources_ok: int = 0
    raw: int = 0
    filtered: Counter = field(default_factory=Counter)
    candidates: int = 0
    from_memory: int = 0
    from_sites: int = 0
    from_official: int = 0       # kanalın kendi sitesinden çözülen adres
    from_extra: int = 0          # famelack vb. JSON veritabanları
    from_siblings: int = 0       # kardeş sunucu adayları (TRT medya↔live …)
    tr_sources: int = 0
    skipped_files: int = 0
    quarantined: int = 0
    tested: int = 0
    deep_tested: int = 0
    status: Counter = field(default_factory=Counter)
    reasons: Counter = field(default_factory=Counter)
    pruned: int = 0
    publish: bool = True
    guard_reason: str = ""
    source_yield: dict = field(default_factory=dict)


# ============================================================== zırhlı liste
def load_armor(reg):
    """zirhli.m3u: (ham_blok, kanallar). Blok tr.m3u'ya BİREBİR yazılır."""
    if not os.path.exists(C.ARMOR_FILE):
        return "", []
    raw = open(C.ARMOR_FILE, encoding="utf-8").read()
    lines = raw.splitlines()
    if lines and lines[0].strip().lstrip("﻿").upper().startswith("#EXTM3U"):
        lines = lines[1:]
    block = "\n".join(lines).strip("\n")
    chans = parse.parse(raw, source=C.ARMOR_FILE)
    for c in chans:
        c.armored = True
        c.raw_name = c.name
        c.name = clean.clean_name(c.name) if not clean.is_junk_name(c.name) else clean.recover_name(c)
        _apply_identity(reg, c)
    log.info("Zırhlı liste: %d kayıt, %d kanal kimliği (silinmez, sağlığı test edilir)",
             len(chans), len({c.cid for c in chans}))
    return block, chans


def _apply_identity(reg, c, source_is_tr=False):
    cid, known = reg.resolve(c, source_is_tr)
    c.cid = cid
    c.group = clean.assign_group(c, reg.meta[cid]["group"] if known else None)
    return known


# ============================================================== adaylar
def fetch_source(item):
    url, kind = item
    txt = get_text(url, timeout=C.HTTP_TIMEOUT)
    if not txt or "#EXTINF" not in txt.upper():
        return url, kind, None
    if any(m in txt[:200000] for m in C.OWN_OUTPUT_MARKERS):
        log.info("Kendi çıktımızın kopyası, atlandı: %s", url)
        return url, "own", []
    return url, kind, parse.parse(txt, source=url)


def gather(reg, opts, st, src_state, url_state, armor_urls):
    pool = []
    if opts.fetch_sources:
        items = sources.collect_all(search=opts.search, source_state=src_state)
        st.sources_total = len(items)
        st.skipped_files = sources.SKIPPED["foreign"]
        with ThreadPoolExecutor(max_workers=C.THREADS_FETCH) as ex:
            for url, kind, chans in ex.map(fetch_source, items):
                src_state.fetched(url, chans is not None, len(chans or []), kind)
                if chans is not None:
                    st.sources_ok += 1
                    pool.extend(chans)
        log.info("Kaynak: %d/%d indirildi · ham kayıt: %d", st.sources_ok, st.sources_total, len(pool))
    else:
        # yalnızca-test modu: mevcut tr.m3u'daki zırhlı olmayan kayıtlar
        if os.path.exists(C.TR_FILE):
            pool = parse.parse(open(C.TR_FILE, encoding="utf-8").read(), source=C.TR_FILE)
    if opts.fetch_sources and C.OFFICIAL_ENABLED:
        off = official.collect()
        pool.extend(off)
        st.from_official = len(off)
    if opts.fetch_sources:
        ext = extra_sources.famelack()
        pool.extend(ext)
        st.from_extra = len(ext)
    if opts.fetch_sites and opts.fetch_sources:
        site_chans = site_providers.collect()
        pool.extend(site_chans)
        st.from_sites = len(site_chans)
        log.info("Site çözücülerinden %d aday (hepsi sağlık testine tabi)", st.from_sites)
    for c in pool:
        c.raw_name = c.name
    # Hafıza: kaynak listesi bu tur gelmese bile son günlerde sağlam olan adresleri tekrar dene.
    # Bunlar da aynı süzgeçlerden geçer (yabancı / radyo / şifreli adresler geri gelmez).
    have = {c.url.strip() for c in pool}
    for rec in url_state.recent_good(include_blocked=not opts.fetch_sources):
        u = rec.get("url", "")
        srcu = rec.get("source") or "memory"
        if (not u or u in have or rec.get("armored") or not rec.get("name")
                or sources.excluded(srcu) or sources.foreign_path(srcu)):
            continue
        c = parse.Channel(name=rec["name"], url=u, logo=rec.get("logo", ""), group="",
                          tvg_id=rec.get("tvg_id", ""), headers=rec.get("headers") or {}, source=srcu)
        c.raw_name = c.name
        c.alive = "memory"
        pool.append(c)
        have.add(u)
    # Kardeş sunucu adayları (TRT medya↔live, Turkuvaz turknet↔trkvz …)
    sib = siblings.expand(list(pool), have)
    pool.extend(sib)
    st.from_siblings = len(sib)
    st.raw = len(pool)

    refined = clean.refine(pool, st.filtered)
    # 1. tur (katı): çok anlamlı adlar Türkiye işareti olmadan eşlenmez
    strict = {id(c): _apply_identity(reg, c) for c in refined}
    # Kaynak "Türk listesi" mi? (kanallarının ≥%25'i kesin Türk kanalı)
    per_src = defaultdict(lambda: [0, 0])
    for c in refined:
        per_src[c.source][0] += 1
        per_src[c.source][1] += strict[id(c)]
    tr_src = {s for s, (n, k) in per_src.items() if n and k / n >= 0.25}
    tr_strong = {s for s, (n, k) in per_src.items() if n >= 5 and k / n >= 0.5}
    st.tr_sources = len(tr_src)
    # 2. tur: Türk listelerindeki kayıtlar artık "NTV", "Star" gibi adlarla da eşlenebilir
    known_map = {id(c): (_apply_identity(reg, c, True) if c.source in tr_src else strict[id(c)])
                 for c in refined}
    out, seen = [], set(armor_urls)
    for c in refined:
        u = c.url.strip()
        if u in seen:
            continue
        known = known_map[id(c)]
        if not reg.tr_relevant(c, known, c.source in tr_strong):
            st.filtered["foreign"] += 1
            continue
        seen.add(u)
        out.append(c)
        if c.alive == "memory":
            st.from_memory += 1
            c.alive = None
    st.candidates = len(out)
    log.info("Aday: %d (hafızadan: %d) · elenen: %s", len(out), st.from_memory, dict(st.filtered))
    return out


def prioritize(cands, reg, url_state, src_state, limit):
    """Sınırdan fazlaysa en değerli adayları seç — ama HER KANALA ADİL PAY vererek.

    Eskiden yalnız puana göre sıralanıyordu: TRT 1 gibi bilinen kanalların yüzlerce
    kopya adresi bütün test bütçesini yiyordu (kanala zaten en fazla 6 kaynak yazılır),
    az bilinen kanallar hiç test edilmiyordu. Şimdi:
      1. tur: her kanaldan en iyi PER_CHANNEL_TEST adayı (kanal sırası da puanla)
      2. tur: kalan bütçe yine puan sırasıyla doldurulur
    """
    if len(cands) <= limit:
        return cands

    def k(c):
        rec = url_state.get(c.url) or {}
        return ((3 if reg.is_known(c.cid) else 0)
                + 2 * src_state.quality(c.source)
                + (rec.get("score", 40) / 25.0)
                + 0.2 * min(clean.tr_score(c), 5)
                + (1.5 if (c.source or "").startswith("official:") else 0))
    ranked = sorted(cands, key=k, reverse=True)
    per = max(1, C.PER_CHANNEL_TEST)
    taken, counts, rest = [], {}, []
    for c in ranked:
        key = c.cid or clean.fold(c.name)
        if counts.get(key, 0) < per:
            counts[key] = counts.get(key, 0) + 1
            taken.append(c)
        else:
            rest.append(c)
    if len(taken) > limit:
        taken = taken[:limit]
    else:
        taken += rest[:limit - len(taken)]
    log.info("Aday sınırı: %d / %d test edilecek (%d kanal, kanal başına önce en iyi %d)",
             len(taken), len(cands), len(counts), per)
    return taken


# ============================================================== test
def _pmap(fn, items, threads, label, until=None):
    """Paralel çalıştır. `until` (epoch sn) geçerse sıradaki işler başlatılmaz;
    sonuç sözlüğünde yalnızca BİTEN işler olur (bitmeyenin anahtarı yoktur)."""
    out = {}
    if not items:
        return out
    done = 0
    t0 = time.time()
    ex = ThreadPoolExecutor(max_workers=threads)
    futs = {ex.submit(fn, it): i for i, it in enumerate(items)}
    try:
        wait_s = None if until is None else max(1.0, until - time.time())
        for f in as_completed(futs, timeout=wait_s):
            i = futs[f]
            try:
                out[i] = f.result()
            except Exception as e:  # tek bir test motoru durdurmasın
                log.debug("test hata: %s", e)
                out[i] = None
            done += 1
            if done % 250 == 0 or done == len(items):
                log.info("  %s: %d/%d (%.0f sn)", label, done, len(items), time.time() - t0)
    except FutTimeout:
        log.warning("  %s: SÜRE DOLDU → %d/%d bitti, kalanı bu tur atlandı (%.0f sn)",
                    label, done, len(items), time.time() - t0)
    # Başlamamış işleri iptal et; sürenler kendi zaman aşımlarıyla kısa sürede biter.
    ex.shutdown(wait=True, cancel_futures=True)
    for f, i in futs.items():   # iptal anında bitmiş olanları da topla
        if i not in out and f.done() and not f.cancelled():
            try:
                out[i] = f.result()
            except Exception:
                out[i] = None
    return out


def test_all(chans, opts, st):
    """Döndürür: (probes, tested) — tested: süre bitmeden test edilebilen sıra numaraları."""
    # Derin test + kayıt için süre bırak.
    reserve = (C.DEEP_RESERVE_MIN * 60 if opts.deep else 0) + 120
    until = budget.deadline() - reserve
    log.info("Hızlı test: %d adres, %d eş zaman · süre bütçesi %.0f dk",
             len(chans), C.THREADS_TEST, max(0, until - time.time()) / 60)
    res = _pmap(lambda c: liveness.probe(c.url, c.headers), chans, C.THREADS_TEST, "hızlı", until)
    tested = set(res)
    probes = [res.get(i) or liveness.Probe(url=c.url, reason="internal") for i, c in enumerate(chans)]
    st.tested = len(tested)

    if opts.progress:
        idx = [i for i, p in enumerate(probes)
               if i in tested and p.status == "ok" and p.kind == "hls"]
        log.info("İlerleme (donma) testi: %d HLS yayın", len(idx))
        _pmap(lambda i: liveness.recheck(probes[i]), idx, C.THREADS_TEST, "ilerleme", until)
    return probes, tested


def deep_pass(chans, probes, url_state, st, opts):
    if not opts.deep:
        return
    if not liveness.ffprobe_available():
        log.warning("ffprobe bulunamadı → derin test atlandı")
        return
    by_cid = defaultdict(list)
    for i, (c, p) in enumerate(zip(chans, probes)):
        if p.ok:
            by_cid[c.cid].append(i)
    picks = []
    for cid, idx in by_cid.items():
        idx.sort(key=lambda i: (probes[i].status == "ok", -probes[i].latency_ms), reverse=True)
        picks.extend(idx[:C.DEEP_PER_CHANNEL])
    picks = picks[:C.DEEP_MAX]
    until = budget.deadline() - 120     # kayıt/yazma için 2 dk bırak
    if until - time.time() < 60:
        log.warning("Derin test için süre kalmadı → atlandı")
        return
    log.info("Derin test (FFprobe): %d adres", len(picks))
    done = _pmap(lambda i: liveness.deep_probe(probes[i]), picks, C.THREADS_DEEP, "derin", until)
    st.deep_tested = len(done)


# ============================================================== birleştir
def assemble(reg, chans, probes, recs):
    """Kanal kimliğine göre grupla: tek kanal + puana göre sıralı kaynaklar."""
    groups = defaultdict(list)
    for c, p, r in zip(chans, probes, recs):
        groups[c.cid].append((c, p, r))

    armor_order = {}
    for c in chans:
        if c.armored and c.cid not in armor_order:
            armor_order[c.cid] = len(armor_order)

    channels = []
    for cid, items in groups.items():
        if not cid:
            continue
        armored = any(c.armored for c, _, _ in items)
        known = reg.is_known(cid)
        meta = reg.meta.get(cid, {})
        names = Counter(c.name for c, _, _ in items)
        logos = Counter(c.logo for c, _, _ in items if c.logo)
        tvg = Counter(c.tvg_id for c, _, _ in items if c.tvg_id)
        grp = Counter(c.group for c, _, _ in items)

        srcs = []
        for c, p, r in items:
            usable = p.ok or (p.status == "blocked" and geo_grace(r))
            sc = r.get("score", 0)
            if not usable and not c.armored:
                continue
            if not c.armored and sc < C.MIN_PUBLISH_SCORE:
                continue
            status = p.status if p.ok else ("geo" if usable else p.status)
            srcs.append({
                "url": c.url, "headers": c.headers or {}, "score": sc, "status": status,
                "reason": p.reason, "latency_ms": p.latency_ms, "kind": p.kind,
                "width": p.width or r.get("width", 0), "height": p.height or r.get("height", 0),
                "vcodec": p.vcodec or r.get("vcodec", ""), "audio": p.has_audio,
                "progress": p.progress, "tls_insecure": p.tls_insecure,
                "armored": c.armored, "last_ok": r.get("last_ok", 0),
                "_m3u_extra": c.extra,
            })
        # iyi olan önce; eşit puanda zırhlı önce
        rank = {"ok": 0, "unstable": 1, "geo": 2}
        srcs.sort(key=lambda s: (rank.get(s["status"], 3), -s["score"], not s["armored"]))
        working = [s for s in srcs if s["status"] in rank]
        if not working and not armored:
            continue
        keep = working[:C.MAX_SOURCES_PER_CHANNEL]
        if armored:   # zırhlı kaynaklar asla düşmez (bozuk olsalar da listede, sonda)
            keep += [s for s in srcs if s["armored"] and s not in keep]
        best = keep[0] if keep and keep[0]["status"] in rank else None
        name = meta.get("name") if known else names.most_common(1)[0][0]
        group = meta.get("group") if known else grp.most_common(1)[0][0]
        gidx = C.GROUP_ORDER.index(group) if group in C.GROUP_ORDER else 99
        channels.append({
            "id": cid,
            "name": name,
            "group": group,
            "logo": meta.get("logo") or (logos.most_common(1)[0][0] if logos else ""),
            "tvg_id": meta.get("tvg_id") or (tvg.most_common(1)[0][0] if tvg else ""),
            "armored": armored,
            "known": known,
            "status": best["status"] if best else "dead",
            "score": best["score"] if best else 0,
            "sources": keep,
            "_order": (0 if armored else 1, armor_order.get(cid, 0), gidx,
                       meta.get("order", 999), name),
        })
    channels.sort(key=lambda ch: ch["_order"])
    return channels


# ============================================================== ana akış
def run(opts=None):
    opts = opts or RunOptions()
    budget.start()
    st = RunStats()
    url_state, src_state = UrlState(), SourceState()
    reg = identity.load_registry(get_json if opts.fetch_sources else None)

    armor_block, armor = load_armor(reg)
    armor_urls = {c.url.strip() for c in armor}
    cands = gather(reg, opts, st, src_state, url_state, armor_urls)

    # karantinadakileri bu tur test etme (zamanı gelince otomatik tekrar denenir)
    active = []
    for c in cands:
        if url_state.quarantined(c.url):
            st.quarantined += 1
        else:
            active.append(c)
    active = prioritize(active, reg, url_state, src_state, opts.max_test)
    to_test = armor + active

    all_urls = {c.url for c in to_test}
    cut_sources = set()   # adreslerinden en az biri süre yüzünden test edilemeyen m3u kaynakları
    probes, tested = test_all(to_test, opts, st)
    if len(tested) < len(to_test):
        cut_sources = {c.source for i, c in enumerate(to_test) if i not in tested}
        # Süre dolduğu için test edilemeyenler "ölü" sayılmasın: hafızaya yazılmaz,
        # bu turun listesine girmez; bir sonraki çalışmada (öncelikli olarak) test edilir.
        log.warning("Süre bütçesi: %d/%d adres test edildi, %d adres sonraki tura kaldı",
                    len(tested), len(to_test), len(to_test) - len(tested))
        keep = sorted(tested)
        to_test = [to_test[i] for i in keep]
        probes = [probes[i] for i in keep]
    deep_pass(to_test, probes, url_state, st, opts)

    recs = [url_state.record(c, p) for c, p in zip(to_test, probes)]
    for p in probes:
        st.status[p.status] += 1
        if not p.ok:
            st.reasons[p.reason.split(":")[0].split(" (")[0]] += 1

    # kaynak verimi: her m3u kaynağı kaç sağlam adres verdi
    yield_ = Counter(c.source for c, p in zip(to_test, probes) if p.ok and not c.armored)
    # Süre yüzünden yarım test edilen kaynağın verimi eksik çıkar → bu tur güncellenmez
    # (yoksa "verimsiz" sanılıp haksız yere karantinaya girerdi).
    for url in {c.source for c in active} - cut_sources:
        if url in src_state.data:
            src_state.yielded(url, yield_.get(url, 0))
    st.source_yield = dict(yield_.most_common(15))

    channels = assemble(reg, to_test, probes, recs)
    healthy = sum(1 for ch in channels if ch["status"] in ("ok", "unstable", "geo"))

    fetch_args = (st.sources_ok, st.sources_total) if opts.fetch_sources else (None, None)
    st.publish, st.guard_reason = guard.check(healthy, *fetch_args)
    st.pruned = url_state.prune(all_urls)

    if opts.dry_run:
        log.info("Deneme modu: dosyalar yazılmadı. Sağlam kanal: %d", healthy)
        return channels, st
    if st.publish or opts.state_only:
        url_state.save()
        src_state.save()
    else:
        # Toplu başarısızlık büyük ihtimalle ağ/GitHub sorunu: hafızaya "ölü" yazıp
        # sağlam adresleri karantinaya sokmayalım.
        log.warning("Koruma devrede → test hafızası da bu tur güncellenmedi")
    if opts.state_only:
        log.info("Yalnızca hafıza güncellendi (bölge: %s). Sağlam kanal: %d", C.REGION, healthy)
        return channels, st
    output.write_all(channels, armor_block, armor, st, healthy, reg)
    log.info("BİTTİ · %d kanal (%d sağlam) · süre %.0f sn", len(channels), healthy, time.time() - st.t0)
    return channels, st
