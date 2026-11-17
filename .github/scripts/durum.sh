#!/usr/bin/env bash
# Motorun hafızası (state/) ana dalda DEĞİL, geçmişi tutulmayan "durum" dalında saklanır.
#
# Neden: state/urls.json ~21 MB ve her çalışmada değişiyor. Ana dala commit'lendiğinde
# git her sürümü sonsuza kadar saklıyor, depo ayda yüzlerce MB büyüyordu; dosya 100 MB'ı
# geçince GitHub push'u reddeder ve liste sessizce güncellenmez olurdu.
#
# Burada: state/ tek bir state.tar.gz olarak (~2 MB) "durum" dalına, TEK commit ile ve her
# seferinde üzerine yazarak (force push) gönderilir. Dalda hiçbir zaman geçmiş birikmez.
# tr.m3u / channels.json / health.json / RAPOR.md eskisi gibi ana dalda kalır.
#
# Kullanım (depo kökünde, actions/checkout sonrası):
#   bash .github/scripts/durum.sh load   # durum dalından state/ klasörünü geri yükler
#   bash .github/scripts/durum.sh save   # state/ klasörünü durum dalına yazar
set -euo pipefail

BRANCH="${DURUM_BRANCH:-durum}"
ARCHIVE="state.tar.gz"

load() {
  if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    git fetch -q --depth=1 origin "$BRANCH"
    local tmp
    tmp="$(mktemp)"
    git show "FETCH_HEAD:$ARCHIVE" > "$tmp"
    rm -rf state
    tar -xzf "$tmp"
    rm -f "$tmp"
    echo "Hafıza '$BRANCH' dalından yüklendi: $(du -sh state | cut -f1)"
  elif [ -d state ]; then
    # İlk geçiş: durum dalı henüz yok, ana dalda eskiden commit'lenmiş state/ kullanılır.
    echo "'$BRANCH' dalı yok; depodaki state/ kullanılıyor (ilk geçiş)."
  else
    echo "Hafıza bulunamadı; motor sıfırdan başlayacak."
    mkdir -p state
  fi
}

save() {
  if [ ! -d state ]; then
    echo "state/ yok; hafıza kaydedilmedi."
    return 0
  fi
  local tmp blob tree commit
  tmp="$(mktemp)"
  tar -czf "$tmp" state
  echo "Hafıza paketi: $(du -h "$tmp" | cut -f1) (state/: $(du -sh state | cut -f1))"
  # Çalışma ağacına ve ana dala dokunmadan, tek dosyalık geçmişsiz bir commit kurulur.
  blob="$(git hash-object -w "$tmp")"
  tree="$(printf '100644 blob %s\t%s\n' "$blob" "$ARCHIVE" | git mktree)"
  commit="$(git commit-tree "$tree" -m "Motor hafızası ($(date -u +'%d-%m-%Y %H:%M') UTC)")"
  rm -f "$tmp"
  for i in 1 2 3; do
    if git push -q -f origin "$commit:refs/heads/$BRANCH"; then
      echo "Hafıza '$BRANCH' dalına yazıldı."
      return 0
    fi
    sleep $((i * 5))
  done
  echo "Hafıza '$BRANCH' dalına yazılamadı." >&2
  return 1
}

case "${1:-}" in
  load) load ;;
  save) save ;;
  *) echo "Kullanım: $0 load|save" >&2; exit 2 ;;
esac
