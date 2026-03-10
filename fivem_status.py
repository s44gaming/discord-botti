"""
FiveM-palvelimen tilan haku. Kokeilee CFX API:a ja suoraa HTTP-endpointia.
"""
import re
import requests

_TIMEOUT = 6
_HEADERS = {"User-Agent": "XevrionBot/1.0"}


def _norm(host: str, port: str) -> tuple[str, str]:
    host = (host or "").strip()
    port = (port or "30120").strip() or "30120"
    if not host:
        return "", port
    host = host.replace("http://", "").replace("https://", "").split("/")[0].strip()
    return host, port


def fetch_fivem_status(host: str, port: str = "30120") -> dict | None:
    """
    Hakee FiveM-palvelimen tilan. Palauttaa dict: hostname, players, max, map, online (bool), error (str)
    tai None jos ei yhteyttä.
    """
    host, port = _norm(host, port)
    if not host:
        return {"online": False, "error": "Palvelin ei ole asetettu."}

    # 1) CFX.re API (palvelin listalla)
    endpoint = f"{host}:{port}"
    try:
        r = requests.get(
            f"https://servers-frontend.fivem.net/api/servers/single/{endpoint}",
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                d = data.get("Data", data)
                if isinstance(d, dict):
                    raw = d.get("hostname") or d.get("vars", {}).get("sv_projectName") or "FiveM"
                    if isinstance(raw, dict):
                        hostname = (raw.get("root") or "FiveM")[:64]
                    else:
                        hostname = (str(raw).strip() or "FiveM")[:64]
                    hostname = re.sub(r"<[^>]+>", "", hostname)[:64]
                    players = int(d.get("clients", 0) or d.get("Players", 0) or 0)
                    max_players = int(d.get("sv_maxclients", 0) or d.get("sv_maxClients", 0) or d.get("MaxPlayers", 48) or 48)
                    return {
                        "online": True,
                        "hostname": hostname[:100] if hostname else "FiveM",
                        "players": players,
                        "max": max_players,
                        "map": (d.get("mapname") or d.get("map", {}).get("name") or "–") if isinstance(d.get("map"), dict) else (d.get("mapname") or d.get("gamename") or "–"),
                        "error": None,
                    }
    except Exception:
        pass

    # 2) Suora info.json / dynamic.json (osa palvelimista tarjoaa)
    for path in ("/info.json", "/dynamic.json"):
        try:
            url = f"http://{host}:{port}{path}"
            r = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
            if r.status_code != 200:
                continue
            data = r.json()
            if not isinstance(data, dict):
                continue
            d = data.get("data", data)
            if not isinstance(d, dict):
                d = data
            hostname = (d.get("hostname") or d.get("vars", {}).get("sv_projectName") or "FiveM")
            if isinstance(hostname, dict):
                hostname = hostname.get("root", "FiveM")
            hostname = (hostname or "FiveM")[:100]
            players = int(d.get("clients", 0) or d.get("Players", 0) or 0)
            max_players = int(d.get("sv_maxclients", 0) or d.get("sv_maxClients", 48) or 48)
            return {
                "online": True,
                "hostname": hostname,
                "players": players,
                "max": max_players,
                "map": (d.get("mapname") or d.get("gamename") or "–"),
                "error": None,
            }
        except Exception:
            continue

    return {"online": False, "error": "Palvelinta ei saatu yhteyttä tai vastaus ei ole tunnistettu."}

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
