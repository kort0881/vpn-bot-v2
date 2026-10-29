"""Добор данных из SQLite, которые появились после основного переноса.

Импортирует poll_answers и недостающие support_messages. Пользователей не
трогает намеренно: в v2 они живут в Postgres, перезапись из SQLite затёрла бы
свежие изменения.

Запуск: ./venv/bin/python scripts/import_delta.py
"""

from __future__ import annotations

import asyncio
import sqlite3

import asyncpg

SQLITE = "/opt/vpn-bot-telegam/data/vpn-bot.db"
PG = dict(host="127.0.0.1", port=5432, user="vpnbot", password="vpnbot_pass_2026", database="vpnbot")


async def main() -> None:
    src = sqlite3.connect(SQLITE)
    src.row_factory = sqlite3.Row
    support = src.execute(
        "SELECT telegram_id, username, full_name, text, created_at, status FROM support_messages"
    ).fetchall()
    polls = src.execute(
        "SELECT poll_id, telegram_id, username, full_name, option_ids FROM poll_answers"
    ).fetchall()
    src.close()

    conn = await asyncpg.connect(**PG)
    added_support = added_polls = 0
    try:
        async with conn.transaction():
            for s in support:
                exists = await conn.fetchval(
                    "SELECT 1 FROM support_messages WHERE telegram_id IS NOT DISTINCT FROM $1 AND created_at=$2",
                    s["telegram_id"],
                    int(s["created_at"] or 0),
                )
                if not exists:
                    await conn.execute(
                        """INSERT INTO support_messages (telegram_id, username, full_name, text, created_at, status)
                           VALUES ($1,$2,$3,$4,$5,$6)""",
                        s["telegram_id"], s["username"], s["full_name"], s["text"],
                        int(s["created_at"] or 0), s["status"] or "new",
                    )
                    added_support += 1

            from collections import Counter
            src_counts = Counter(
                (p["poll_id"], p["telegram_id"], p["option_ids"]) for p in polls
            )
            rows = await conn.fetch("SELECT poll_id, telegram_id, option_ids FROM poll_answers")
            pg_counts = Counter((r["poll_id"], r["telegram_id"], r["option_ids"]) for r in rows)
            for p in polls:
                key = (p["poll_id"], p["telegram_id"], p["option_ids"])
                if pg_counts.get(key, 0) >= src_counts[key]:
                    continue
                await conn.execute(
                    """INSERT INTO poll_answers (poll_id, telegram_id, username, full_name, option_ids)
                       VALUES ($1,$2,$3,$4,$5)""",
                    p["poll_id"], p["telegram_id"], p["username"], p["full_name"], p["option_ids"],
                )
                pg_counts[key] = pg_counts.get(key, 0) + 1
                added_polls += 1

        print("добавлено support:", added_support, "| poll_answers:", added_polls)
        for table in ("users", "payments", "support_messages", "poll_answers"):
            print(f"  {table}: {await conn.fetchval(f'SELECT count(*) FROM {table}')}")
        print("в SQLite:", {
            "support": len(support),
            "polls": len(polls),
        })
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
