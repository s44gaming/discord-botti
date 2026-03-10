# Discord Bot - Monipalvelin-hallinta

Python-pohjainen Discord-botti, joka tukee useaa palvelinta ja web-käyttöliittymää palvelinkohtaisten asetusten hallintaan. Vain ylläpitäjät voivat hallita asetuksia.

## Ominaisuudet

- **Monipalvelin** – sama botti usealla serverillä, kaikki asetukset palvelinkohtaisia
- **Web-dashboard** – hallitse kaikkia ominaisuuksia palvelin kerrallaan
- **Ylläpitäjä-tarkistus** – vain palvelimen Administratorit näkevät hallinnan
- **Peruskomentoja** – ping, info, tervehdys, hallinta
- **Moderaatio** – kick, ban, mute, varoitukset, purge – roolit ja toiminnat hallitaan webistä
- **Serverilogit** – mod-toiminnot, jäsenet liittyy/poistuu, viestien poisto/muokkaus – kanava ja tyypit webistä
- **Tikettijärjestelmä** – staff-rooli, kategoria ja kanava määritellään webistä

## Vaatimukset

- **Python 3.8+** (suositellaan 3.10 tai uudempi)
- **Paketit**:
  - discord.py >= 2.7.1
  - flask >= 3.0.0
  - requests >= 2.31.0
  - python-dotenv >= 1.0.0

Vapaaehtoinen: `discord.py[speed]` nopeampaan JSON-käsittelyyn ja parempaan suorituskykyyn.

## Nopea käynnistys

### 1. Asenna riippuvuudet

```bash
pip install -r requirements.txt
```

### 2. Luo Discord-sovellus

1. Mene [Discord Developer Portal](https://discord.com/developers/applications)
2. **New Application** → anna nimi
3. Vasemmalla **Bot** → **Reset Token** → kopioi token
4. Ota käyttöön: **Message Content Intent** ja **Server Members Intent** (mod-roolit, serverilogit)
5. Vasemmalla **OAuth2** → kopioi **Client ID** ja **Client Secret**
6. **OAuth2 → Redirects** → lisää: `http://localhost:5000/callback`

### 3. Kutsu botti palvelimelle

1. **OAuth2 → URL Generator**
2. Valitse scopet: `bot`, `applications.commands`
3. Valitse bot-oikeudet: `Administrator` (tai vähintään: Manage Channels, Kick/Ban Members, Moderate Members, Manage Messages)
4. Kopioi generoitu URL ja avaa selaimessa
5. Valitse palvelin ja hyväksy

### 4. Konfiguroi ympäristö

1. Kopioi `.env.example` → `.env`
2. Täytä arvot:

```env
DISCORD_TOKEN=botin_token_tähän
DISCORD_CLIENT_ID=sovelluksen_client_id
DISCORD_CLIENT_SECRET=client_secret
DISCORD_REDIRECT_URI=http://localhost:5000/callback

# Tärkeää: Luo satunnainen avain!
FLASK_SECRET_KEY=generate_a_random_secret_key
```

**FLASK_SECRET_KEY**: Luo turvallinen satunnainen avain esim. komennolla:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Kopioi tulos ja käytä sitä `FLASK_SECRET_KEY`-arvona.

### 5. Käynnistä botti

```bash
python run.py
```

Tämä käynnistää:
- Discord-botin (slash-komennot)
- Web-dashboardin osoitteessa: http://localhost:5000

---

## Web-dashboard

1. Avaa http://localhost:5000
2. **Kirjaudu Discordilla** – tarvitaan Discord-tili
3. Valitse palvelin – näkyvät vain palvelimet, joilla sinulla on **Administrator**-oikeudet
4. Hallitse asetuksia – muutokset astuvat voimaan heti

### Webissä hallittavat asetukset (palvelinkohtaisesti)

| Osa | Asetukset |
|-----|-----------|
| **Perusominaisuudet** | Ping, Info, Tervehdys, Hallinta-linkki, Tikettijärjestelmä – päälle/pois |
| **Moderaatio** | Moderaattoriroolit (ketkä voivat käyttää mod-komentoja), yksittäisten mod-toimintojen päälle/pois |
| **Logit** | Logikanava, lokityypit (mod-toiminnot, jäsen liittyy/poistuu, viestin poisto/muokkaus) |
| **Tiketit** | Staff-rooli (ketkä näkevät tiketit), kategoria tiketille, kanava josta tiketti avataan |

---

## Slash-komennot

### Peruskomentoja

| Komento | Kuvaus |
|---------|--------|
| `/ping` | Botin vastausaika |
| `/info` | Palvelimen tiedot |
| `/tervehdys` | Tervehdys |
| `/hallinta` | Linkki web-dashboardiin |

### Moderaatiokomennot

| Komento | Kuvaus |
|---------|--------|
| `/kick` | Potkaise jäsen palvelimelta |
| `/ban` | Estä jäsen palvelimelta |
| `/mute` | Mykistä jäsen (timeout) |
| `/unmute` | Poista mykistys |
| `/varoitus` | Anna varoitus jäsenelle |
| `/varoitukset` | Näytä jäsenen varoitukset |
| `/poista_varoitukset` | Poista kaikki varoitukset jäseneltä |
| `/purge` | Poista viestejä kanavalta |

*Mod-roolit määritellään webissä. Ylläpitäjillä on aina mod-oikeudet.*

### Tikettijärjestelmä

| Komento | Kuvaus |
|---------|--------|
| `/tiketti_paneeli` | Lähettää "Avaa tiketti" -viestin webistä valituille kanavalle (vain ylläpitäjille) |

**Miten tikettijärjestelmä toimii**

1. **Aseta web-dashboardissa** (Tikettijärjestelmä -osio):
   - **Rooli joka näkee tiketit** – rooli (esim. Staff), joka pääsee vastaamaan tikeille
   - **Kategoria tiketille** – kategoria johon uudet tiketit luodaan
   - **Kanava josta tiketti avataan** – kanava johon "Avaa tiketti" -viesti lähetetään
2. **Ota Tikettijärjestelmä käyttöön** (Perusominaisuudet -osio)
3. **Suorita Discordissa** `/tiketti_paneeli` – botti lähettää viestin valitulle kanavalle
4. **Käyttäjät** painavat "Avaa tiketti" -nappia → luodaan yksityinen kanava (vain avaaja + staff näkevät)
5. **Staff** vastaa tiketissa ja voi sulkea sen "Sulje tiketti" -napilla

---

Kaikki ominaisuudet voidaan ottaa pois käytöstä web-dashboardista palvelin kerrallaan.

## Projektin rakenne

```
DiscordBotti/
├── LICENSE
├── run.py              # Käynnistys (botti + web)
├── bot.py              # Discord-botin logiikka
├── web_app.py          # Flask web-sovellus
├── database.py         # Tietokanta (SQLite)
├── config.py           # Konfiguraatio
├── logs.py             # Logien lähetys kanavalle
├── requirements.txt
├── .env.example
├── commands/           # Slash-komennot
│   ├── ping.py
│   ├── info.py
│   ├── tervehdys.py
│   ├── hallinta.py
│   ├── moderaatio.py   # kick, ban, mute, varoitukset, purge
│   └── tiketti.py      # Tikettijärjestelmä
├── events/
│   ├── on_ready.py
│   └── server_logs.py  # join/leave, viestin poisto/muokkaus
├── web/
│   ├── templates/      # HTML-sivut
│   └── static/         # CSS, JS
└── data/               # Luodaan automaattisesti (tietokanta)
```

## Tuotantokäyttö

- Vaihda `BASE_URL` ja `DISCORD_REDIRECT_URI` tuotannon domainiin
- Käytä vahvaa `FLASK_SECRET_KEY`-arvoa
- Harkitse HTTPS:ää ja reverse-proxyä (esim. Nginx)
- Voit käyttää Gunicornia web-sovellukselle erillisessä prosessissa

## Tuki ja yhteisö

Jos tarvitset apua botin kanssa, liity [S44Gaming Squad](https://discord.gg/ujB4JHfgcg) Discord-palvelimelle ja lähetä viesti kanavalle **#tukitiketti**.

## Lisenssi

Katso [LICENSE](LICENSE). Tekijän oikeudet: S44Gaming. Ei-kaupallinen käyttö sallittu; kaupallinen käyttö vain S44Gaming:n suostumuksella.
