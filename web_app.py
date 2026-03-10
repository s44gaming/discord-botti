import os
import secrets
import requests
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from functools import wraps
import database

_REQ_TIMEOUT = 10
_REQ_HEADERS = {"User-Agent": "DiscordBot (Web Dashboard)"}

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["PERMANENT_SESSION_LIFETIME"] = 86400

DISCORD_API = "https://discord.com/api/v10"
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

AVAILABLE_FEATURES = [
    ("ping", "Ping", "Ping-komento vastausajan tarkistukseen"),
    ("info", "Info", "Palvelimen tiedot -komento"),
    ("tervehdys", "Tervehdys", "Tervehdys-komento"),
    ("hallinta", "Hallinta-linkki", "Linkki web-hallintapaneeliin"),
    ("tiketti", "Tikettijärjestelmä", "Tiketit ja tiketti-paneeli"),
]

MOD_FEATURES = [
    ("kick", "Kick", "Potkaise jäsen"),
    ("ban", "Ban", "Estä jäsen"),
    ("mute", "Mute", "Mykistä (timeout)"),
    ("unmute", "Unmute", "Poista mykistys"),
    ("warn", "Varoitus", "Varoitus/varoitukset/poisto"),
    ("purge", "Purge", "Poista viestejä"),
]

LOG_FEATURES = [
    ("mod_actions", "Moderaatiotoiminnot", "Kick/ban/mute/warn/purge -lokit"),
    ("member_join", "Jäsen liittyy", "Lokita kun jäsen liittyy"),
    ("member_leave", "Jäsen poistuu", "Lokita kun jäsen poistuu"),
    ("message_delete", "Viestin poisto", "Lokita viestin poisto"),
    ("message_edit", "Viestin muokkaus", "Lokita viestin muokkaus"),
]


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def get_user_guilds():
    token = session.get("access_token")
    if not token:
        return []
    r = requests.get(
        f"{DISCORD_API}/users/@me/guilds",
        headers={"Authorization": f"Bearer {token}", **_REQ_HEADERS},
        timeout=_REQ_TIMEOUT
    )
    if r.status_code != 200:
        return []
    guilds = r.json()
    ADMIN = 0x8
    return [g for g in guilds if (int(g.get("permissions", 0) or 0) & ADMIN) == ADMIN]


def get_guild_channels(guild_id: str) -> list:
    """Hakee palvelimen tekstikanavat bot-tokenilla. Bottin pitää olla palvelimella."""
    if not BOT_TOKEN:
        return []
    r = requests.get(
        f"{DISCORD_API}/guilds/{guild_id}/channels",
        headers={"Authorization": f"Bot {BOT_TOKEN}", **_REQ_HEADERS},
        timeout=_REQ_TIMEOUT
    )
    if r.status_code != 200:
        return []
    channels = [c for c in r.json() if c.get("type") == 0]
    return sorted(channels, key=lambda x: (x.get("position", 0), x["name"]))


def get_guild_categories(guild_id: str) -> list:
    """Hakee palvelimen kategoriat (type 4)."""
    if not BOT_TOKEN:
        return []
    r = requests.get(
        f"{DISCORD_API}/guilds/{guild_id}/channels",
        headers={"Authorization": f"Bot {BOT_TOKEN}", **_REQ_HEADERS},
        timeout=_REQ_TIMEOUT
    )
    if r.status_code != 200:
        return []
    cats = [c for c in r.json() if c.get("type") == 4]
    return sorted(cats, key=lambda x: (x.get("position", 0), x["name"]))

def get_guild_roles(guild_id: str) -> list:
    """Hakee roolit bot-tokenilla. Bottin pitää olla palvelimella."""
    if not BOT_TOKEN:
        return []
    r = requests.get(
        f"{DISCORD_API}/guilds/{guild_id}",
        headers={"Authorization": f"Bot {BOT_TOKEN}", **_REQ_HEADERS},
        timeout=_REQ_TIMEOUT
    )
    if r.status_code != 200:
        return []
    roles = r.json().get("roles", [])
    # poista managed-roolit (bot roolit)
    roles = [ro for ro in roles if not ro.get("managed")]
    return sorted(roles, key=lambda x: x.get("position", 0), reverse=True)


@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html", base_url=BASE_URL)


@app.route("/login")
def login():
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify guilds"
        f"&state={state}"
    )
    return redirect(url)


@app.route("/callback")
def callback():
    if request.args.get("state") != session.get("oauth_state"):
        return "Virhe: Väärä tila", 400
    code = request.args.get("code")
    if not code:
        return "Virhe: Koodi puuttuu", 400
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    r = requests.post(f"{DISCORD_API}/oauth2/token", data=data, timeout=_REQ_TIMEOUT)
    if r.status_code != 200:
        return f"Virhe kirjautumisessa: {r.text}", 400
    token_data = r.json()
    session["access_token"] = token_data["access_token"]
    session["refresh_token"] = token_data.get("refresh_token")
    session.permanent = True
    r = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {token_data['access_token']}", **_REQ_HEADERS},
        timeout=_REQ_TIMEOUT
    )
    if r.status_code != 200:
        return "Virhe käyttäjätietojen haussa", 400
    session["user"] = r.json()
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    guilds = get_user_guilds()
    return render_template("dashboard.html", guilds=guilds, user=session["user"])


@app.route("/guild/<guild_id>")
@login_required
def guild_settings(guild_id):
    guilds = get_user_guilds()
    guild = next((g for g in guilds if g["id"] == guild_id), None)
    if not guild:
        return "Sinulla ei ole ylläpito-oikeuksia tähän palvelimeen.", 403
    settings = database.get_guild_settings(guild_id)
    features = []
    for key, label, desc in AVAILABLE_FEATURES:
        features.append({
            "key": key,
            "label": label,
            "description": desc,
            "enabled": settings.get(key, True)
        })
    channels = [{"id": c["id"], "name": c["name"]} for c in get_guild_channels(guild_id)]
    categories = [{"id": c["id"], "name": c["name"]} for c in get_guild_categories(guild_id)]
    roles = [{"id": r["id"], "name": r["name"]} for r in get_guild_roles(guild_id)]
    mod_roles = settings.get("mod_roles", [])
    ticket_staff_role = settings.get("ticket_staff_role_id")
    ticket_category = settings.get("ticket_category_id")
    ticket_channel = settings.get("ticket_channel_id")
    mod_features = [{
        "key": k,
        "label": l,
        "description": d,
        "enabled": settings.get(f"mod_{k}", True)
    } for k, l, d in MOD_FEATURES]
    log_features = [{
        "key": k,
        "label": l,
        "description": d,
        "enabled": settings.get(f"log_{k}", True)
    } for k, l, d in LOG_FEATURES]
    log_channel = settings.get("log_channel_id") or settings.get("mod_log_channel_id")
    welcome_enabled = settings.get("welcome_enabled", False)
    welcome_channel = settings.get("welcome_channel_id")
    return render_template(
        "guild_settings.html",
        guild=guild,
        features=features,
        mod_features=mod_features,
        roles=roles,
        mod_roles=mod_roles,
        log_features=log_features,
        channels=channels,
        log_channel=log_channel,
        categories=categories,
        ticket_staff_role=ticket_staff_role,
        ticket_category=ticket_category,
        ticket_channel=ticket_channel,
        welcome_enabled=welcome_enabled,
        welcome_channel=welcome_channel,
        user=session["user"]
    )


@app.route("/api/guild/<guild_id>/feature/<feature>", methods=["POST"])
@login_required
def toggle_feature(guild_id, feature):
    guilds = get_user_guilds()
    if not any(g["id"] == guild_id for g in guilds):
        return jsonify({"error": "Ei oikeuksia"}), 403
    valid_keys = [f[0] for f in AVAILABLE_FEATURES]
    if feature not in valid_keys:
        return jsonify({"error": "Tuntematon ominaisuus"}), 400
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", True))
    settings = database.update_feature(guild_id, feature, enabled)
    return jsonify({"success": True, "settings": settings})


@app.route("/api/guild/<guild_id>/mod/log-channel", methods=["POST"])
@login_required
def api_set_mod_log_channel(guild_id):
    guilds = get_user_guilds()
    if not any(g["id"] == guild_id for g in guilds):
        return jsonify({"error": "Ei oikeuksia"}), 403
    data = request.get_json() or {}
    channel_id = data.get("channel_id")
    database.set_log_channel(guild_id, str(channel_id) if channel_id else None)
    return jsonify({"success": True})

@app.route("/api/guild/<guild_id>/mod/roles", methods=["POST"])
@login_required
def api_set_mod_roles(guild_id):
    guilds = get_user_guilds()
    if not any(g["id"] == guild_id for g in guilds):
        return jsonify({"error": "Ei oikeuksia"}), 403
    data = request.get_json() or {}
    role_ids = data.get("role_ids", [])
    database.set_mod_roles(guild_id, role_ids if isinstance(role_ids, list) else [])
    return jsonify({"success": True})


@app.route("/api/guild/<guild_id>/mod/feature/<action>", methods=["POST"])
@login_required
def api_toggle_mod_feature(guild_id, action):
    guilds = get_user_guilds()
    if not any(g["id"] == guild_id for g in guilds):
        return jsonify({"error": "Ei oikeuksia"}), 403
    valid = [x[0] for x in MOD_FEATURES]
    if action not in valid:
        return jsonify({"error": "Tuntematon ominaisuus"}), 400
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", True))
    database.set_mod_action_enabled(guild_id, action, enabled)
    return jsonify({"success": True})


@app.route("/api/guild/<guild_id>/logs/feature/<log_key>", methods=["POST"])
@login_required
def api_toggle_log_feature(guild_id, log_key):
    guilds = get_user_guilds()
    if not any(g["id"] == guild_id for g in guilds):
        return jsonify({"error": "Ei oikeuksia"}), 403
    valid = [x[0] for x in LOG_FEATURES]
    if log_key not in valid:
        return jsonify({"error": "Tuntematon ominaisuus"}), 400
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", True))
    database.set_log_enabled(guild_id, log_key, enabled)
    return jsonify({"success": True})


@app.route("/api/guild/<guild_id>/welcome/settings", methods=["POST"])
@login_required
def api_set_welcome_settings(guild_id):
    guilds = get_user_guilds()
    if not any(g["id"] == guild_id for g in guilds):
        return jsonify({"error": "Ei oikeuksia"}), 403
    data = request.get_json() or {}
    enabled = bool(data["enabled"]) if "enabled" in data else None
    channel_id = None
    if "channel_id" in data:
        ch = data["channel_id"]
        channel_id = str(ch) if ch else ""  # "" = tyhjennä kanava
    database.set_welcome_settings(guild_id, enabled=enabled, channel_id=channel_id)
    return jsonify({"success": True})


@app.route("/api/guild/<guild_id>/ticket/settings", methods=["POST"])
@login_required
def api_set_ticket_settings(guild_id):
    guilds = get_user_guilds()
    if not any(g["id"] == guild_id for g in guilds):
        return jsonify({"error": "Ei oikeuksia"}), 403
    data = request.get_json() or {}
    staff_role = data.get("staff_role_id") or ""
    category = data.get("category_id") or ""
    channel = data.get("channel_id") or ""
    database.set_ticket_settings(guild_id, staff_role_id=staff_role, category_id=category, channel_id=channel)
    return jsonify({"success": True})


def create_app():
    return app
