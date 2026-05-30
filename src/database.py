"""SQLite persistence layer for SentinelWatch.

Hybrid approach:
- In-memory stores for fast reads (no change to existing code)
- Write-through to SQLite for persistence across restarts
- WAL mode for concurrent read/write performance
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = "sentinelwatch.db"

# In-memory stores (mirrored to SQLite on mutations)
_findings_db: List[Dict[str, Any]] = []
_alerts_db: List[Dict[str, Any]] = []
_entities_db: List[Dict[str, Any]] = []
_investigations_db: List[Dict[str, Any]] = []
_scans_db: List[Dict[str, Any]] = []

# Locks per table for concurrent safety
_locks = {
    "findings": asyncio.Lock(),
    "alerts": asyncio.Lock(),
    "entities": asyncio.Lock(),
    "investigations": asyncio.Lock(),
    "scans": asyncio.Lock(),
}

TABLE_NAMES = {"findings", "alerts", "entities", "investigations", "scans"}

_connection: Optional[aiosqlite.Connection] = None


def _validate_table(table: str) -> None:
    """Validate that the table name is in the whitelist."""
    if table not in TABLE_NAMES:
        raise ValueError(f"Invalid table name: {table}")


# ── Initialization ───────────────────────────────────────────── #

async def init_db() -> None:
    """Create tables and load existing data into memory."""
    global _connection
    _connection = await aiosqlite.connect(DB_PATH)
    _connection.row_factory = aiosqlite.Row

    # Enable WAL mode for concurrent read/write performance
    await _connection.execute("PRAGMA journal_mode=WAL")
    await _connection.execute("PRAGMA synchronous=NORMAL")
    await _connection.execute("PRAGMA cache_size=-8000")  # 8MB cache

    await _create_tables()
    await _load_all()
    logger.info(f"Database initialized: {DB_PATH}")


async def _create_tables() -> None:
    """Create tables if they don't exist."""
    await _connection.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    await _connection.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    await _connection.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    await _connection.execute("""
        CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    await _connection.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    await _connection.commit()


async def _load_all() -> None:
    """Load all data from SQLite into in-memory stores."""
    _findings_db.clear()
    _alerts_db.clear()
    _entities_db.clear()
    _investigations_db.clear()
    _scans_db.clear()

    rows = await _connection.execute_fetchall("SELECT data FROM findings")
    for row in rows:
        _findings_db.append(json.loads(row[0]))

    rows = await _connection.execute_fetchall("SELECT data FROM alerts")
    for row in rows:
        _alerts_db.append(json.loads(row[0]))

    rows = await _connection.execute_fetchall("SELECT data FROM entities")
    for row in rows:
        _entities_db.append(json.loads(row[0]))

    rows = await _connection.execute_fetchall("SELECT data FROM investigations")
    for row in rows:
        _investigations_db.append(json.loads(row[0]))

    rows = await _connection.execute_fetchall("SELECT data FROM scans")
    for row in rows:
        _scans_db.append(json.loads(row[0]))

    logger.info(
        f"Loaded: {len(_findings_db)} findings, {len(_alerts_db)} alerts, "
        f"{len(_entities_db)} entities, {len(_investigations_db)} investigations, "
        f"{len(_scans_db)} scans"
    )


async def close_db() -> None:
    """Close the database connection."""
    global _connection
    if _connection:
        await _connection.close()
        _connection = None
        logger.info("Database connection closed")


# ── Write-through helpers ────────────────────────────────────── #

async def _upsert(table: str, record: Dict[str, Any]) -> None:
    """Insert or replace a record in the given table."""
    _validate_table(table)
    rid = record.get("id", "")
    data = json.dumps(record, default=str)
    async with _locks.get(table, asyncio.Lock()):
        await _connection.execute(
            f"INSERT OR REPLACE INTO {table} (id, data) VALUES (?, ?)",
            (rid, data),
        )
        await _connection.commit()


async def _delete(table: str, record_id: str) -> None:
    """Delete a record from the given table."""
    _validate_table(table)
    async with _locks.get(table, asyncio.Lock()):
        await _connection.execute(
            f"DELETE FROM {table} WHERE id = ?", (record_id,)
        )
        await _connection.commit()


async def _clear_table(table: str) -> None:
    """Delete all records from the given table."""
    _validate_table(table)
    async with _locks.get(table, asyncio.Lock()):
        await _connection.execute(f"DELETE FROM {table}")
        await _connection.commit()


# ── Public API ───────────────────────────────────────────────── #

# Findings
async def save_finding(finding: Dict[str, Any]) -> None:
    await _upsert("findings", finding)

async def delete_finding(finding_id: str) -> None:
    await _delete("findings", finding_id)

async def clear_findings() -> None:
    await _clear_table("findings")


# Alerts
async def save_alert(alert: Dict[str, Any]) -> None:
    await _upsert("alerts", alert)

async def clear_alerts() -> None:
    await _clear_table("alerts")


# Entities
async def save_entity(entity: Dict[str, Any]) -> None:
    await _upsert("entities", entity)

async def clear_entities() -> None:
    await _clear_table("entities")


# Investigations
async def save_investigation(investigation: Dict[str, Any]) -> None:
    await _upsert("investigations", investigation)

async def clear_investigations() -> None:
    await _clear_table("investigations")


# Scans
async def save_scan(scan: Dict[str, Any]) -> None:
    await _upsert("scans", scan)

async def clear_scans() -> None:
    await _clear_table("scans")


# Bulk save (for seed data)
async def bulk_save(table: str, records: List[Dict[str, Any]]) -> None:
    """Save multiple records efficiently."""
    _validate_table(table)
    if not records:
        return
    async with _locks.get(table, asyncio.Lock()):
        await _connection.executemany(
            f"INSERT OR REPLACE INTO {table} (id, data) VALUES (?, ?)",
            [(r.get("id", ""), json.dumps(r, default=str)) for r in records],
        )
        await _connection.commit()
