"""Clipboard history storage: SQLite metadata + PNG files for images."""
from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "clipboard_data"
DB_PATH = DATA_DIR / "history.db"
IMG_DIR = DATA_DIR / "images"
MAX_ITEMS = 200


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT,
            image_file TEXT,
            preview TEXT,
            created_at REAL NOT NULL
        )
        """
    )
    return conn


def add_text(text: str) -> None:
    text = text.strip()
    if not text:
        return
    with _conn() as conn:
        row = conn.execute("SELECT content FROM history ORDER BY id DESC LIMIT 1").fetchone()
        if row and row[0] == text:
            return
        conn.execute(
            "INSERT INTO history (type, content, preview, created_at) VALUES ('text', ?, ?, ?)",
            (text, text[:200], time.time()),
        )
    _trim()


def add_image(png_bytes: bytes) -> None:
    digest = hashlib.sha1(png_bytes).hexdigest()
    with _conn() as conn:
        row = conn.execute(
            "SELECT content FROM history WHERE type='image' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row and row[0] == digest:
            return
        filename = f"{int(time.time() * 1000)}.png"
        (IMG_DIR / filename).write_bytes(png_bytes)
        conn.execute(
            "INSERT INTO history (type, content, image_file, preview, created_at) VALUES ('image', ?, ?, ?, ?)",
            (digest, filename, "[image]", time.time()),
        )
    _trim()


def _trim() -> None:
    with _conn() as conn:
        rows = conn.execute("SELECT id, image_file FROM history ORDER BY id DESC").fetchall()
        for rid, img in rows[MAX_ITEMS:]:
            if img:
                (IMG_DIR / img).unlink(missing_ok=True)
            conn.execute("DELETE FROM history WHERE id=?", (rid,))


def list_items(limit: int = 100) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, type, preview, image_file, created_at FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"id": r[0], "type": r[1], "preview": r[2], "image_file": r[3], "created_at": r[4]}
        for r in rows
    ]


def get_item(item_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT type, content, image_file FROM history WHERE id=?", (item_id,)
        ).fetchone()
    if not row:
        return None
    return {"type": row[0], "content": row[1], "image_file": row[2]}


def delete_item(item_id: int) -> None:
    item = get_item(item_id)
    if not item:
        return
    if item["image_file"]:
        (IMG_DIR / item["image_file"]).unlink(missing_ok=True)
    with _conn() as conn:
        conn.execute("DELETE FROM history WHERE id=?", (item_id,))


def clear_all() -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM history")
    for f in IMG_DIR.glob("*.png"):
        f.unlink(missing_ok=True)
