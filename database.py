import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")

DEFAULT_MOD_FEATURES = {
    "kick": True,
    "ban": True,
    "mute": True,
    "unmute": True,
    "warn": True,
    "purge": True,
}

DEFAULT_LOG_FEATURES = {
    "mod_actions": True,
    "member_join": True,
    "member_leave": True,
    "message_delete": True,
    "message_edit": True,
}


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id TEXT PRIMARY KEY,
            features TEXT DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            discriminator TEXT,
            avatar TEXT,
            access_token TEXT,
            refresh_token TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            mod_id TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_guild_settings(guild_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT features FROM guild_settings WHERE guild_id = ?", (str(guild_id),))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return {}


def set_guild_settings(guild_id: str, features: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO guild_settings (guild_id, features, updated_at) VALUES (?, ?, datetime('now'))",
        (str(guild_id), json.dumps(features))
    )
    conn.commit()
    conn.close()


def update_feature(guild_id: str, feature: str, enabled: bool) -> dict:
    settings = get_guild_settings(guild_id)
    settings[feature] = enabled
    set_guild_settings(guild_id, settings)
    return settings


def is_feature_enabled(guild_id: str, feature: str) -> bool:
    settings = get_guild_settings(guild_id)
    return settings.get(feature, True)


def get_log_channel(guild_id: str) -> str | None:
    """Palauttaa logikanavan ID:n tai None (takautuvasti mod_log_channel_id)."""
    settings = get_guild_settings(guild_id)
    ch = settings.get("log_channel_id") or settings.get("mod_log_channel_id")
    return str(ch) if ch else None


def set_log_channel(guild_id: str, channel_id: str | None) -> None:
    """Asettaa logikanavan. channel_id=None poistaa valinnan."""
    settings = get_guild_settings(guild_id)
    if channel_id:
        settings["log_channel_id"] = str(channel_id)
    else:
        settings.pop("log_channel_id", None)
    set_guild_settings(guild_id, settings)


def get_mod_roles(guild_id: str) -> list[str]:
    settings = get_guild_settings(guild_id)
    roles = settings.get("mod_roles", [])
    if not isinstance(roles, list):
        return []
    return [str(r) for r in roles]


def set_mod_roles(guild_id: str, role_ids: list) -> None:
    settings = get_guild_settings(guild_id)
    if not isinstance(role_ids, list):
        role_ids = []
    settings["mod_roles"] = [str(r) for r in role_ids]
    set_guild_settings(guild_id, settings)


def is_mod_action_enabled(guild_id: str, action: str) -> bool:
    settings = get_guild_settings(guild_id)
    return bool(settings.get(f"mod_{action}", DEFAULT_MOD_FEATURES.get(action, True)))


def set_mod_action_enabled(guild_id: str, action: str, enabled: bool) -> None:
    settings = get_guild_settings(guild_id)
    settings[f"mod_{action}"] = bool(enabled)
    set_guild_settings(guild_id, settings)


def is_log_enabled(guild_id: str, log_key: str) -> bool:
    settings = get_guild_settings(guild_id)
    return bool(settings.get(f"log_{log_key}", DEFAULT_LOG_FEATURES.get(log_key, True)))


def set_log_enabled(guild_id: str, log_key: str, enabled: bool) -> None:
    settings = get_guild_settings(guild_id)
    settings[f"log_{log_key}"] = bool(enabled)
    set_guild_settings(guild_id, settings)


def add_warn(guild_id: str, user_id: str, mod_id: str, reason: str = "") -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO warns (guild_id, user_id, mod_id, reason) VALUES (?, ?, ?, ?)",
        (str(guild_id), str(user_id), str(mod_id), (reason or "Ei syytä")),
    )
    warn_id = c.lastrowid
    conn.commit()
    conn.close()
    return int(warn_id or 0)


def get_user_warns(guild_id: str, user_id: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, mod_id, reason, created_at FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC",
        (str(guild_id), str(user_id)),
    )
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "mod_id": r[1], "reason": r[2], "created_at": r[3]} for r in rows]


def get_ticket_settings(guild_id: str) -> dict:
    """Palauttaa tiketti-asetukset: staff_role_id, category_id, channel_id."""
    settings = get_guild_settings(guild_id)
    return {
        "staff_role_id": settings.get("ticket_staff_role_id"),
        "category_id": settings.get("ticket_category_id"),
        "channel_id": settings.get("ticket_channel_id"),
    }


def get_welcome_settings(guild_id: str) -> dict:
    """Palauttaa tervetuloa-asetukset: enabled, channel_id."""
    settings = get_guild_settings(guild_id)
    return {
        "enabled": bool(settings.get("welcome_enabled", False)),
        "channel_id": settings.get("welcome_channel_id"),
    }


def set_welcome_settings(guild_id: str, enabled: bool | None = None, channel_id: str | None = None) -> None:
    s = get_guild_settings(guild_id)
    if enabled is not None:
        s["welcome_enabled"] = bool(enabled)
    if channel_id is not None:
        if channel_id:
            s["welcome_channel_id"] = str(channel_id)
        else:
            s.pop("welcome_channel_id", None)
    set_guild_settings(guild_id, s)


def set_ticket_settings(guild_id: str, staff_role_id: str | None = None, category_id: str | None = None, channel_id: str | None = None) -> None:
    s = get_guild_settings(guild_id)
    if staff_role_id is not None:
        if staff_role_id:
            s["ticket_staff_role_id"] = str(staff_role_id)
        else:
            s.pop("ticket_staff_role_id", None)
    if category_id is not None:
        if category_id:
            s["ticket_category_id"] = str(category_id)
        else:
            s.pop("ticket_category_id", None)
    if channel_id is not None:
        if channel_id:
            s["ticket_channel_id"] = str(channel_id)
        else:
            s.pop("ticket_channel_id", None)
    set_guild_settings(guild_id, s)


def clear_warns(guild_id: str, user_id: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM warns WHERE guild_id = ? AND user_id = ?", (str(guild_id), str(user_id)))
    deleted = int(c.rowcount or 0)
    conn.commit()
    conn.close()
    return deleted
