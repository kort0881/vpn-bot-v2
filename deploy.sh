#!/usr/bin/env bash
# Деплой бота: бэкап → проверка синтаксиса → рестарт → самопроверка.
set -euo pipefail
ROOT=/opt/vpn-bot-v2
TS=$(date +%Y%m%d_%H%M%S)

echo "[1/4] бэкап"
tar -czf /root/vpn-bot-backup-$TS.tgz -C /opt vpn-bot-v2/source vpn-bot-v2/.env 2>/dev/null || true

echo "[2/4] проверка синтаксиса"
$ROOT/venv/bin/python -m compileall -q $ROOT/source || { echo "СИНТАКСИС СЛОМАН — не деплою"; exit 1; }

echo "[3/4] рестарт"
systemctl restart vpn-bot
sleep 8
systemctl is-active vpn-bot

echo "[4/4] журнал (ошибки за минуту)"
journalctl -u vpn-bot --since "1 min ago" --no-pager | grep -iE "error|traceback" || echo "ошибок нет"
