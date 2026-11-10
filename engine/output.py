# -*- coding: utf-8 -*-
"""Çıktılar: tr.m3u · channels.json · health.json · RAPOR.md"""
import logging
import os
import shutil
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import config as C
from . import guard
from .health import atomic_write, dump_json, iso, now_ts
from .parse import Channel

log = logging.getLogger("output")
OK_SET = ("ok", "unstable", "geo")
TR_TZ = timezone(timedelta(hours=3))


def _stamp():
    return datetime.now(TR_TZ).strftime("%d-%m-%Y %H:%M")


def _public_source(s):
    return {k: v for k, v in s.items() if not k.startswith("_")}


def _public_channel(ch):
    d = {k: v for k, v in ch.items() if not k.startswith("_")}
    d["sources"] = [_public_source(s) for s in ch["sources"]]
    return d


# ------------------------------------------------------------------ tr.m3u
def armor_entries(armor):
    """Zırhlı kayıtlar: ad/logo/adres/başlık/sıra aynen, yalnızca grup adı düzeltilmiş."""
    return [c.to_m3u(name=c.raw_name or c.name) for c in armor]


def build_m3u(channels, armor_block, armor=None):
    head = "#EXTM3U"
    if C.EPG_URLS:
        head += f' x-tvg-url="{",".join(C.EPG_URLS)}"'
    parts = [head]
    if armor and C.ARMOR_NORMALIZE_GROUPS:
        parts.extend(armor_entries(armor))
    elif armor_block:
        parts.append(armor_block)
    lines, n = [], 0
    for ch in channels:
        working = [s for s in ch["sources"] if s["status"] in OK_SET]
        if ch["armored"]:
            if any(s["armored"] for s in working):
                continue                       # zırhlı kayıt zaten sağlam
            extra = [s for s in working if not s["armored"]][:1]
            labels = [f'{ch["name"]} (Otomatik)']
        else:
            extra = working[:1 + C.M3U_BACKUPS]
            labels = [ch["name"]] + [f'{ch["name"]} (Yedek {i})' for i in range(1, len(extra))]
        for s, label in zip(extra, labels):
            c = Channel(name=label, url=s["url"], logo=ch["logo"], group=ch["group"],
                        tvg_id=ch["tvg_id"], extra=s.get("_m3u_extra") or [],
                        headers=s["headers"])
            lines.append(c.to_m3u())
            n += 1
    parts.append(f"# --- GÜNCEL CANLI LİSTE ({_stamp()}) · {n} kayıt --- #")
    parts.extend(lines)
    return "\n".join(parts) + "\n", n


# ------------------------------------------------------------------ json
def build_channels_json(channels, st, healthy):
    return {
        "version": 2,
        "generated_at": iso(now_ts()),
        "region": C.REGION,
        "epg": C.EPG_URLS,
        "stats": {
            "channels": len(channels),
            "healthy_channels": healthy,
            "sources": sum(len(c["sources"]) for c in channels),
            "armored_channels": sum(1 for c in channels if c["armored"]),
        },
        "channels": [_public_channel(c) for c in channels],
    }


def build_health_json(channels, st, healthy):
    armored = [c for c in channels if c["armored"]]
    return {
        "generated_at": iso(now_ts()),
        "region": C.REGION,
        "published": st.publish,
        "guard": st.guard_reason,
        "totals": {
            "channels": len(channels), "healthy_channels": healthy,
            "tested_urls": st.tested, "deep_tested": st.deep_tested,
            "status": dict(st.status), "candidates": st.candidates,
            "quarantined": st.quarantined, "site_candidates": st.from_sites, "sources_ok": st.sources_ok,
            "sources_total": st.sources_total,
        },
        "armored": {
            "channels": len(armored),
            "healthy": sum(1 for c in armored if c["status"] in OK_SET),
            "rescued_by_auto": sum(1 for c in armored
                                   if c["status"] in OK_SET and not c["sources"][0]["armored"]),
        },
        "channels": [{
            "id": c["id"], "name": c["name"], "group": c["group"], "status": c["status"],
            "score": c["score"], "armored": c["armored"],
            "ok_sources": sum(1 for s in c["sources"] if s["status"] in OK_SET),
            "sources": len(c["sources"]),
        } for c in channels],
        "top_sources": st.source_yield,
        "dead_reasons": dict(st.reasons.most_common(12)),
    }


# ------------------------------------------------------------------ rapor
def build_report(channels, st, healthy, m3u_n, armor, reg):
    dur = int(datetime.now().timestamp() - st.t0)
    armored = [c for c in channels if c["armored"]]
    a_ok = [c for c in armored if c["status"] in OK_SET]
    a_dead = [c for c in armored if c["status"] not in OK_SET]
    a_rescued = [c for c in a_ok if not c["sources"][0]["armored"]]
    a_cred = sum(1 for c in armor if _has_cred(c.url))
    groups = Counter(c["group"] for c in channels if c["status"] in OK_SET)
    multi = sum(1 for c in channels if sum(s["status"] in OK_SET for s in c["sources"]) >= 2)
    stat = st.status
    R = ["# PuuStream IPTV Motoru — Güncelleme Raporu",
         "",
         f"**Tarih:** {_stamp()} (TSİ) · **Test bölgesi:** {C.REGION} · **Süre:** {dur // 60} dk {dur % 60} sn",
         "",
         ("✅ **Yayınlandı.** " if st.publish else "🛡️ **YAYIN DURDURULDU — eski sağlam liste korundu.** ")
         + f"Koruma: {st.guard_reason}",
         "",
         "## Özet",
         "",
         "| | |", "|---|---|",
         f"| Sağlam kanal (en az 1 çalışan kaynak) | **{healthy}** |",
         f"| Yedek kaynağı olan kanal (≥2 sağlam) | {multi} |",
         f"| tr.m3u otomatik bölüm kaydı | {m3u_n} |",
         f"| Test edilen adres | {st.tested} (derin/FFprobe: {st.deep_tested}) |",
         f"| Sonuç | ✅ {stat.get('ok', 0)} sağlam · ⚠️ {stat.get('unstable', 0)} kararsız · "
         f"🚫 {stat.get('blocked', 0)} engelli · ❌ {stat.get('dead', 0)} ölü |",
         f"| Karantinada (bu tur atlandı) | {st.quarantined} |",
         f"| Kaynak listesi | {st.sources_ok}/{st.sources_total} indirildi |",
         f"| Site çözücüleri (7 spor kaynağı) | {st.from_sites} aday (sağlık testine tabi) |",
         f"| Aday (hafızadan geri çağrılan) | {st.candidates} ({st.from_memory}) |",
         f"| Türk listesi sayılan kaynak | {st.tr_sources} |",
         f"| Yabancı olduğu için indirilmeyen dosya | {st.skipped_files} |",
         f"| Elenen | {', '.join(f'{k}: {v}' for k, v in st.filtered.items()) or '-'} |",
         "",
         "## Zırhlı kanallar",
         "",
         f"- Kimlik: **{len(armored)}** kanal ({len(armor)} kayıt)",
         f"- Sağlam: **{len(a_ok)}** · Çalışmayan: **{len(a_dead)}**",
         f"- Kendi adresi bozuk ama otomatik yedekle kurtarılan: **{len(a_rescued)}**",
         ]
    if a_cred:
        R.append(f"- ⚠️ Zırhlı listede kullanıcı adı/şifre içeren **{a_cred}** adres var. "
                 "Depo herkese açıksa bu hesap bilgileri herkes tarafından görülebilir.")
    if a_dead:
        R += ["", "<details><summary>Çalışmayan zırhlı kanallar</summary>", ""]
        for c in a_dead[:150]:
            why = Counter(s["reason"] for s in c["sources"]).most_common(1)
            R.append(f"- {c['name']} — {len(c['sources'])} kayıt · {why[0][0] if why else '?'}")
        R += ["", "</details>"]
    R += ["", "## Gruplara göre sağlam kanallar", ""]
    for g, n in sorted(groups.items(), key=lambda x: -x[1]):
        R.append(f"- **{g}:** {n}")
    R += ["", "## En iyi 20 kanal (puan)", "", "| Kanal | Puan | Sağlam kaynak | Çözünürlük | Açılış |",
          "|---|---|---|---|---|"]
    top = sorted([c for c in channels if c["status"] in OK_SET], key=lambda c: -c["score"])[:20]
    for c in top:
        s = c["sources"][0]
        res = f"{s['height']}p" if s.get("height") else "?"
        R.append(f"| {c['name']} | {c['score']} | {sum(x['status'] in OK_SET for x in c['sources'])} "
                 f"| {res} | {s['latency_ms']} ms |")
    if st.source_yield:
        R += ["", "## En verimli kaynaklar", ""]
        for u, n in st.source_yield.items():
            R.append(f"- {n} sağlam · `{u}`")
    if st.reasons:
        R += ["", "## Ölü/engelli nedenleri", ""]
        for r, n in st.reasons.most_common(12):
            R.append(f"- {r}: {n}")
    R += ["", f"_iptv-org ile zenginleştirilen kanal: {reg.enriched}_", ""]
    return "\n".join(R)


def _has_cred(url):
    from .clean import has_credentials
    return has_credentials(url)


# ------------------------------------------------------------------ yaz
def write_all(channels, armor_block, armor, st, healthy, reg):
    m3u, m3u_n = build_m3u(channels, armor_block, armor)
    if st.publish:
        if os.path.exists(C.TR_FILE):
            shutil.copyfile(C.TR_FILE, C.TR_FILE + ".bak")
        atomic_write(C.TR_FILE, m3u)
        dump_json(C.CHANNELS_FILE, build_channels_json(channels, st, healthy), compact=True)
        os.makedirs(C.LAST_GOOD_DIR, exist_ok=True)
        for f in (C.TR_FILE, C.CHANNELS_FILE):
            shutil.copyfile(f, os.path.join(C.LAST_GOOD_DIR, os.path.basename(f)))
        guard.remember({"at": iso(now_ts()), "healthy_channels": healthy,
                        "channels": len(channels), "m3u_entries": m3u_n})
        log.info("Yayınlandı → %s (%d otomatik kayıt), %s", C.TR_FILE, m3u_n, C.CHANNELS_FILE)
    else:
        log.warning("Koruma devrede: %s ve %s DEĞİŞTİRİLMEDİ", C.TR_FILE, C.CHANNELS_FILE)
    dump_json(C.HEALTH_FILE, build_health_json(channels, st, healthy))
    atomic_write(C.REPORT_FILE, build_report(channels, st, healthy, m3u_n, armor, reg))
