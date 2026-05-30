"""Persistence layer for SentinelWatch.

Hybrid approach:
- In-memory stores for fast reads
- Write-through to SQLite (local) or PostgreSQL (Railway/production)
- Auto-detects backend from DATABASE_URL
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = "sentinelwatch.db"

_DATABASE_URL = os.environ.get("DATABASE_URL", "")
_USE_POSTGRES = _DATABASE_URL.startswith("postgresql")

_findings_db: List[Dict[str, Any]] = []
_alerts_db: List[Dict[str, Any]] = []
_entities_db: List[Dict[str, Any]] = []
_investigations_db: List[Dict[str, Any]] = []
_scans_db: List[Dict[str, Any]] = []

_locks = {
    "findings": asyncio.Lock(),
    "alerts": asyncio.Lock(),
    "entities": asyncio.Lock(),
    "investigations": asyncio.Lock(),
    "scans": asyncio.Lock(),
}

TABLE_NAMES = {"findings", "alerts", "entities", "investigations", "scans"}

_sqlite_conn = None
_pg_pool = None


def _validate_table(table: str) -> None:
    if table not in TABLE_NAMES:
        raise ValueError(f"Invalid table name: {table}")


async def init_db() -> None:
    if _USE_POSTGRES:
        await _init_postgres()
    else:
        await _init_sqlite()
    await _load_all()
    backend = "PostgreSQL" if _USE_POSTGRES else "SQLite"
    logger.info(f"Database initialized ({backend})")


async def _init_sqlite() -> None:
    import aiosqlite

    global _sqlite_conn
    _sqlite_conn = await aiosqlite.connect(DB_PATH)
    _sqlite_conn.row_factory = aiosqlite.Row

    await _sqlite_conn.execute("PRAGMA journal_mode=WAL")
    await _sqlite_conn.execute("PRAGMA synchronous=NORMAL")
    await _sqlite_conn.execute("PRAGMA cache_size=-8000")

    for table in TABLE_NAMES:
        await _sqlite_conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
    await _sqlite_conn.commit()


async def _init_postgres() -> None:
    import asyncpg

    global _pg_pool
    _pg_pool = await asyncpg.create_pool(
        _DATABASE_URL, min_size=1, max_size=5
    )

    async with _pg_pool.acquire() as conn:
        for table in TABLE_NAMES:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    data JSONB NOT NULL
                )
            """)


async def _load_all() -> None:
    _findings_db.clear()
    _alerts_db.clear()
    _entities_db.clear()
    _investigations_db.clear()
    _scans_db.clear()

    if _USE_POSTGRES:
        async with _pg_pool.acquire() as conn:
            for table, store in [
                ("findings", _findings_db),
                ("alerts", _alerts_db),
                ("entities", _entities_db),
                ("investigations", _investigations_db),
                ("scans", _scans_db),
            ]:
                rows = await conn.fetch(f"SELECT data FROM {table}")
                for row in rows:
                    store.append(dict(row["data"]))
    else:
        import aiosqlite

        for table, store in [
            ("findings", _findings_db),
            ("alerts", _alerts_db),
            ("entities", _entities_db),
            ("investigations", _investigations_db),
            ("scans", _scans_db),
        ]:
            rows = await _sqlite_conn.execute_fetchall(f"SELECT data FROM {table}")
            for row in rows:
                store.append(json.loads(row[0]))

    logger.info(
        f"Loaded: {len(_findings_db)} findings, {len(_alerts_db)} alerts, "
        f"{len(_entities_db)} entities, {len(_investigations_db)} investigations, "
        f"{len(_scans_db)} scans"
    )


async def close_db() -> None:
    global _sqlite_conn, _pg_pool

    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None
        logger.info("PostgreSQL pool closed")

    if _sqlite_conn:
        await _sqlite_conn.close()
        _sqlite_conn = None
        logger.info("SQLite connection closed")


async def _upsert(table: str, record: Dict[str, Any]) -> None:
    _validate_table(table)
    rid = record.get("id", "")
    data = json.dumps(record, default=str)

    if _USE_POSTGRES:
        async with _locks.get(table, asyncio.Lock()):
            async with _pg_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO {} (id, data) VALUES ($1, $2::jsonb) "
                    "ON CONFLICT (id) DO UPDATE SET data = $2::jsonb".format(table),
                    rid, data,
                )
    else:
        async with _locks.get(table, asyncio.Lock()):
            await _sqlite_conn.execute(
                "INSERT OR REPLACE INTO {} (id, data) VALUES (?, ?)".format(table),
                (rid, data),
            )
            await _sqlite_conn.commit()


async def _delete(table: str, record_id: str) -> None:
    _validate_table(table)
    async with _locks.get(table, asyncio.Lock()):
        if _USE_POSTGRES:
            async with _pg_pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM {} WHERE id = $1".format(table), record_id
                )
        else:
            await _sqlite_conn.execute(
                "DELETE FROM {} WHERE id = ?".format(table), (record_id,)
            )
            await _sqlite_conn.commit()


async def _clear_table(table: str) -> None:
    _validate_table(table)
    async with _locks.get(table, asyncio.Lock()):
        if _USE_POSTGRES:
            async with _pg_pool.acquire() as conn:
                await conn.execute("DELETE FROM {}".format(table))
        else:
            await _sqlite_conn.execute("DELETE FROM {}".format(table))
            await _sqlite_conn.commit()


async def save_finding(finding: Dict[str, Any]) -> None:
    await _upsert("findings", finding)

async def delete_finding(finding_id: str) -> None:
    await _delete("findings", finding_id)

async def clear_findings() -> None:
    await _clear_table("findings")

async def save_alert(alert: Dict[str, Any]) -> None:
    await _upsert("alerts", alert)

async def clear_alerts() -> None:
    await _clear_table("alerts")

async def save_entity(entity: Dict[str, Any]) -> None:
    await _upsert("entities", entity)

async def clear_entities() -> None:
    await _clear_table("entities")

async def save_investigation(investigation: Dict[str, Any]) -> None:
    await _upsert("investigations", investigation)

async def clear_investigations() -> None:
    await _clear_table("investigations")

async def save_scan(scan: Dict[str, Any]) -> None:
    await _upsert("scans", scan)

async def clear_scans() -> None:
    await _clear_table("scans")


async def bulk_save(table: str, records: List[Dict[str, Any]]) -> None:
    _validate_table(table)
    if not records:
        return

    async with _locks.get(table, asyncio.Lock()):
        if _USE_POSTGRES:
            async with _pg_pool.acquire() as conn:
                await conn.executemany(
                    "INSERT INTO {} (id, data) VALUES ($1, $2::jsonb) "
                    "ON CONFLICT (id) DO UPDATE SET data = $2::jsonb".format(table),
                    [(r.get("id", ""), json.dumps(r, default=str)) for r in records],
                )
        else:
            import aiosqlite
            await _sqlite_conn.executemany(
                "INSERT OR REPLACE INTO {} (id, data) VALUES (?, ?)".format(table),
                [(r.get("id", ""), json.dumps(r, default=str)) for r in records],
            )
            await _sqlite_conn.commit()
