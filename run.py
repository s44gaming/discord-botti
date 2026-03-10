#!/usr/bin/env python3
"""
Discord Bot + Web Dashboard - Käynnistys yhdellä tiedostolla.
Käynnistää sekä Discord-botin että Flask web-käyttöliittymän.
"""
import os
import sys
import threading

# Lataa .env ennen muita importteja
from dotenv import load_dotenv
load_dotenv()

# Varmista FLASK_SECRET_KEY
if not os.getenv("FLASK_SECRET_KEY") or os.getenv("FLASK_SECRET_KEY") == "generate_a_random_secret_key":
    import secrets
    key = secrets.token_hex(32)
    print(f"\n⚠️  FLASK_SECRET_KEY puuttuu .env-tiedostosta!")
    print(f"   Lisää tämä rivi .env-tiedostoon: FLASK_SECRET_KEY={key}\n")
    os.environ["FLASK_SECRET_KEY"] = key

import database
from config import DISCORD_TOKEN, WEB_PORT
from bot import create_bot
from web_app import app
import shared_state

shared_state.capture_console()


def run_web():
    database.init_db()
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False, use_reloader=False, threaded=True)


def run_bot():
    bot = create_bot()
    shared_state.set_bot(bot)
    bot.run(DISCORD_TOKEN)


def main():
    database.init_db()

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    print(f"Web-dashboard käynnissä: http://localhost:{WEB_PORT}")
    run_web()


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Virhe: Aseta DISCORD_TOKEN .env-tiedostoon.")
        sys.exit(1)
    main()

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
