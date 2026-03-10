"""
Botin tiedot: kuvaus, kehittäjät, kutsu-linkki.
Tiedosto on salasanasuojattu – muokkaus vain kehittäjäportaalista oikealla salasanalla.
"""
import os
import json
import base64
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_PLAIN_FILE = _BASE / "data" / "bot_info.txt"
_ENC_FILE = _BASE / "data" / "bot_info.enc"
_SALT = b"bot_info_s44gaming_v1"  # kiinteä suola, sama salasana tuottaa aina saman avaimen


def _derive_key(password: str) -> bytes:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=120000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def load(edit_password: str | None = None) -> dict | None:
    """
    Lataa botin tiedot. edit_password tarvitaan vain salatun tiedoston lukemiseen.
    Palauttaa {"description": str, "developers": list[str], "invite_link": str} tai None.
    """
    # 1) Salattu tiedosto (vaatii salasanan)
    if _ENC_FILE.exists() and edit_password:
        try:
            from cryptography.fernet import Fernet
            key = _derive_key(edit_password)
            f = Fernet(key)
            raw = _ENC_FILE.read_bytes()
            data = json.loads(f.decrypt(raw).decode("utf-8"))
            return {
                "description": data.get("description", "").strip(),
                "developers": [x.strip() for x in data.get("developers", []) if x.strip()],
                "invite_link": (data.get("invite_link") or "").strip(),
                "apply_bot_url": (data.get("apply_bot_url") or "").strip(),
            }
        except Exception:
            return None
    # 2) Plain-tiedosto (alkuperäinen, ei salasanaa)
    if _PLAIN_FILE.exists():
        try:
            desc, devs, invite, apply_url = "", [], "", ""
            for line in _PLAIN_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip()
                    if k == "BOT_DESCRIPTION":
                        desc = v
                    elif k == "BOT_DEVELOPERS":
                        devs = [x.strip() for x in v.split(",") if x.strip()]
                    elif k == "BOT_INVITE_LINK":
                        invite = v
                    elif k == "BOT_APPLY_URL":
                        apply_url = v
            return {"description": desc, "developers": devs, "invite_link": invite, "apply_bot_url": apply_url}
        except Exception:
            return None
    return None


def save(data: dict, edit_password: str) -> bool:
    """
    Tallentaa botin tiedot salattuun tiedostoon. Vain oikealla salasanalla.
    data: {"description": str, "developers": list[str], "invite_link": str}
    """
    try:
        from cryptography.fernet import Fernet
        key = _derive_key(edit_password)
        f = Fernet(key)
        payload = json.dumps({
            "description": data.get("description", ""),
            "developers": data.get("developers", []),
            "invite_link": data.get("invite_link", ""),
            "apply_bot_url": data.get("apply_bot_url", ""),
        }, ensure_ascii=False).encode("utf-8")
        _ENC_FILE.parent.mkdir(parents=True, exist_ok=True)
        _ENC_FILE.write_bytes(f.encrypt(payload))
        return True
    except Exception:
        return False


def encrypted_file_exists() -> bool:
    return _ENC_FILE.exists()

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
