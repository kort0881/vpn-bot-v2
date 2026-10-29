"""Перенос данных старого бота (SQLite) в новую БД (PostgreSQL).

Идемпотентен: users обновляются по user_id, payments/support/stats дополняются
без дублей. Запуск:  ./venv/bin/python scripts/import_legacy.py
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timezone

import asyncpg

SQLITE = "/opt/vpn-bot-telegam/data/vpn-bot.db"
PG = dict(host="127.0.0.1", port=5432, user="vpnbot", password="vpnbot_pass_2026", database="vpnbot")


def ms_to_dt(value: int | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def parse_links(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (TypeError, ValueError):
        return []


async def main() -> None:
    src = sqlite3.connect(SQLITE)
    src.row_factory = sqlite3.Row

    users = src.execute("SELECT * FROM users").fetchall()
    payments = src.execute("SELECT * FROM payments").fetchall()
    support = src.execute("SELECT * FROM support_messages").fetchall()
    stats = src.execute("SELECT * FROM stats").fetchall()
    src.close()

    conn = await asyncpg.connect(**PG)
    try:
        async with conn.transaction():
            for u in users:
                await conn.execute(
                    """
                    INSERT INTO users (
                        user_id, username, language_code, email, client_uuid, vless_link, links,
                        total_bytes, used_bytes, expiry_at, is_active, banned, unsubscribed_at,
                        channel_step, chosen_channel, ban_reason, ban_at, created_at, updated_at
                    ) VALUES (
                        $1,$2,'ru',$3,$4,$5,$6::jsonb,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,COALESCE($17, now()),now()
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        email = EXCLUDED.email,
                        client_uuid = EXCLUDED.client_uuid,
                        vless_link = EXCLUDED.vless_link,
                        links = EXCLUDED.links,
                        total_bytes = EXCLUDED.total_bytes,
                        used_bytes = EXCLUDED.used_bytes,
                        expiry_at = EXCLUDED.expiry_at,
                        is_active = EXCLUDED.is_active,
                        banned = EXCLUDED.banned,
                        unsubscribed_at = EXCLUDED.unsubscribed_at,
                        channel_step = EXCLUDED.channel_step,
                        chosen_channel = EXCLUDED.chosen_channel,
                        ban_reason = EXCLUDED.ban_reason,
                        ban_at = EXCLUDED.ban_at,
                        updated_at = now()
                    """,
                    int(u["telegram_id"]),
                    u["username"] or "",
                    u["email"],
                    u["client_uuid"],
                    u["vless_link"],
                    json.dumps(parse_links(u["links"])),
                    int(u["total_bytes"] or 0),
                    float(u["used_bytes"] or 0.0),
                    int(u["expiry_at"] or 0),
                    bool(u["is_active"]),
                    bool(u["banned"]),
                    int(u["unsubscribed_at"] or 0),
                    int(u["channel_step"] or 0),
                    int(u["chosen_channel"] if u["chosen_channel"] is not None else -1),
                    u["ban_reason"] or "",
                    int(u["ban_at"] or 0),
                    ms_to_dt(u["created_at"]),
                )

            for p in payments:
                exists = await conn.fetchval(
                    "SELECT 1 FROM payments WHERE telegram_id=$1 AND created_at=$2 AND amount=$3",
                    int(p["telegram_id"]), int(p["created_at"] or 0), int(p["amount"] or 0),
                )
                if not exists:
                    await conn.execute(
                        """INSERT INTO payments (telegram_id, username, full_name, amount, method, status, created_at, confirmed_at)
                           VALUES ($1,$2,$3,$4,$5,$6,$7,$8)""",
                        int(p["telegram_id"]), p["username"] or "", p["full_name"] or "",
                        int(p["amount"] or 0), p["method"] or "sbp", p["status"] or "claimed",
                        int(p["created_at"] or 0), int(p["confirmed_at"] or 0),
                    )

            for s in support:
                exists = await conn.fetchval(
                    "SELECT 1 FROM support_messages WHERE telegram_id=$1 AND created_at=$2",
                    s["telegram_id"], int(s["created_at"] or 0),
                )
                if not exists:
                    await conn.execute(
                        """INSERT INTO support_messages (telegram_id, username, full_name, text, created_at, status)
                           VALUES ($1,$2,$3,$4,$5,$6)""",
                        s["telegram_id"], s["username"], s["full_name"], s["text"],
                        int(s["created_at"] or 0), s["status"] or "new",
                    )

            for st in stats:
                await conn.execute(
                    """INSERT INTO stats (key, value) VALUES ($1,$2)
                       ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
                    st["key"], int(st["value"] or 0),
                )

        counts = {}
        for table in ("users", "payments", "support_messages", "stats"):
            counts[table] = await conn.fetchval(f"SELECT count(*) FROM {table}")
        print("Перенесено:", counts)
        print("SQLite было:", {"users": len(users), "payments": len(payments),
                               "support_messages": len(support), "stats": len(stats)})
        row = await conn.fetchrow(
            "SELECT user_id, username, email, expiry_at, is_active, banned, jsonb_array_length(links) AS links "
            "FROM users ORDER BY user_id LIMIT 1"
        )
        print("Пример записи:", dict(row) if row else "нет")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
