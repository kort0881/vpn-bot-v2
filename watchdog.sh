#!/usr/bin/env bash
# Внешний сторож: бот жив, панель отвечает, шлюз отдаёт подписку.
# При сбое — рестарт сервиса + алерт админу в Telegram.
set -uo pipefail
ENV=/opt/vpn-bot-v2/.env
LOG=/var/log/vpn-bot-watchdog.log
TOKEN=$(grep -E '^BOT_TOKEN=' $ENV | cut -d= -f2-)
ADMIN=$(grep -E '^ADMIN_ID=' $ENV | cut -d= -f2-)
SUB=$(grep -E '^SUB_URL=' $ENV | cut -d= -f2- | sed 's/{user_id}/1/')
fail=0
say() { echo "$(date '+%F %T') $*" >> $LOG; }
alert() { echo "$(date '+%F %T') [bot_watchdog] $1" >> /var/log/ops_alerts.log; }

if ! systemctl is-active --quiet vpn-bot; then
  say "bot не активен — рестарт"
  systemctl restart vpn-bot; sleep 10
  if systemctl is-active --quiet vpn-bot; then
    alert "🔧 Сторож: бот был мёртв, поднял заново."
  else
    alert "🛑 Сторож: бот мёртв и не поднимается. Нужен человек."
    exit 1
  fi
fi

# 01-11-26: 522 у Cloudflare бывает транзиентным (origin секунду недоступен).
# Три попытки с паузой — иначе сторож будил владельца на ровном месте.
code=000
for try in 1 2 3; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -A 'watchdog' "$SUB")
  [ "$code" = "200" ] && break
  [ "$try" -lt 3 ] && sleep 15
done
if [ "$code" != "200" ]; then
  say "шлюз подписки HTTP $code (после 3 попыток)"
  fail=1
fi

if [ $fail -eq 1 ]; then
  alert "⚠️ Сторож: шлюз подписки отвечает HTTP ${code}. Проверь панель/CDN."
fi
say "ок (sub=$code)"
