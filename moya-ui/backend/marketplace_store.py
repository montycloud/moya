"""Pluggable persistence for the Agent Marketplace."""

from __future__ import annotations

import json
import os
import pathlib
import sqlite3
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class AgentListing(BaseModel):
    id: str
    name: str
    description: str = ''
    tags: list[str] = Field(default_factory=list)
    category: str = 'General'
    provider: str = 'user'
    node_count: dict[str, int] = Field(default_factory=dict)
    flow: dict[str, Any]
    published_at: str


class MarketplaceStore(ABC):
    @abstractmethod
    def list_agents(self) -> list[AgentListing]: ...

    @abstractmethod
    def get_agent(self, agent_id: str) -> AgentListing | None: ...

    @abstractmethod
    def publish_agent(self, listing: AgentListing) -> AgentListing: ...

    @abstractmethod
    def delete_agent(self, agent_id: str) -> bool: ...


class JsonFileMarketplaceStore(MarketplaceStore):
    def __init__(self, path: pathlib.Path | str | None = None):
        if path is None:
            path = pathlib.Path(__file__).parent / 'marketplace.json'
        self._path = pathlib.Path(path)

    def _read(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text())
        except (json.JSONDecodeError, OSError):
            return []

    def _write(self, data: list[dict]) -> None:
        self._path.write_text(json.dumps(data, indent=2))

    def list_agents(self) -> list[AgentListing]:
        return [AgentListing(**d) for d in self._read()]

    def get_agent(self, agent_id: str) -> AgentListing | None:
        for d in self._read():
            if d.get('id') == agent_id:
                return AgentListing(**d)
        return None

    def publish_agent(self, listing: AgentListing) -> AgentListing:
        data = self._read()
        data = [d for d in data if d.get('id') != listing.id]
        data.append(listing.model_dump())
        self._write(data)
        return listing

    def delete_agent(self, agent_id: str) -> bool:
        data = self._read()
        new_data = [d for d in data if d.get('id') != agent_id]
        removed = len(new_data) < len(data)
        self._write(new_data)
        return removed


class SqliteMarketplaceStore(MarketplaceStore):
    def __init__(self, path: pathlib.Path | str | None = None):
        if path is None:
            path = pathlib.Path(__file__).parent / 'marketplace.db'
        self._path = str(path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id           TEXT PRIMARY KEY,
                    name         TEXT NOT NULL,
                    description  TEXT DEFAULT '',
                    tags         TEXT DEFAULT '[]',
                    category     TEXT DEFAULT 'General',
                    provider     TEXT DEFAULT 'user',
                    node_count   TEXT DEFAULT '{}',
                    flow         TEXT NOT NULL,
                    published_at TEXT NOT NULL
                )
            ''')
            conn.commit()

    def list_agents(self) -> list[AgentListing]:
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT * FROM agents ORDER BY published_at DESC'
            ).fetchall()
        return [self._row_to_listing(r) for r in rows]

    def get_agent(self, agent_id: str) -> AgentListing | None:
        with self._connect() as conn:
            row = conn.execute(
                'SELECT * FROM agents WHERE id = ?', (agent_id,)
            ).fetchone()
        return self._row_to_listing(row) if row else None

    def publish_agent(self, listing: AgentListing) -> AgentListing:
        with self._connect() as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO agents
                     (id, name, description, tags, category, provider,
                      node_count, flow, published_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    listing.id, listing.name, listing.description,
                    json.dumps(listing.tags), listing.category, listing.provider,
                    json.dumps(listing.node_count), json.dumps(listing.flow),
                    listing.published_at,
                ),
            )
            conn.commit()
        return listing

    def delete_agent(self, agent_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute('DELETE FROM agents WHERE id = ?', (agent_id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_listing(row: sqlite3.Row) -> AgentListing:
        return AgentListing(
            id=row['id'],
            name=row['name'],
            description=row['description'] or '',
            tags=json.loads(row['tags'] or '[]'),
            category=row['category'] or 'General',
            provider=row['provider'] or 'user',
            node_count=json.loads(row['node_count'] or '{}'),
            flow=json.loads(row['flow']),
            published_at=row['published_at'],
        )


def get_store() -> MarketplaceStore:
    """Factory: reads MARKETPLACE_STORE env var — 'sqlite' or 'json' (default)."""
    if os.environ.get('MARKETPLACE_STORE', '').lower() == 'sqlite':
        return SqliteMarketplaceStore()
    return JsonFileMarketplaceStore()
