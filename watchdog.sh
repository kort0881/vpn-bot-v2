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
alert() { curl -s --max-time 15 "https://api.telegram.org/bot${TOKEN}/sendMessage"   -d "chat_id=${ADMIN}" -d "text=$1" >/dev/null 2>&1; }

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

code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -A 'watchdog' "$SUB")
if [ "$code" != "200" ]; then
  say "шлюз подписки HTTP $code"
  fail=1
fi

if [ $fail -eq 1 ]; then
  alert "⚠️ Сторож: шлюз подписки отвечает HTTP ${code}. Проверь панель/CDN."
fi
say "ок (sub=$code)"
