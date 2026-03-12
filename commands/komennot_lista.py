"""
Näyttää kaikki käytettävissä olevat slash-komennot. Päivittyy automaattisesti kun komentoja lisätään.
Näyttää jokaiselle Päällä/Pois-tilan (web-asetuksista).
"""
import discord
from discord import app_commands
from discord.ext import commands

# Komento -> feature-avain (web-hallinnan COMMAND_FEATURES)
COMMAND_TO_FEATURE = {
    "ping": "ping",
    "info": "info",
    "hallinta": "hallinta",
    "lähetäkutsu": "kutsuviesti",
    "taso": "taso",
    "kolikko": "kolikko",
    "8ball": "8ball",
    "arvaa_luku": "arvaa",
    "ruletti": "ruletti",
    "afk": "afk",
    "muistutus": "muistutus",
    "komennot": "komennot_lista",
    "tervehdys": "tervehdys",
    "kutsu": "kutsu",
    "tiketti_paneeli": "tiketti",
    "tasonboard": "tasonboard",
    "noppa": "noppa",
    "kps": "kps",
    "arpa": "arpa",
    "fivem": "fivem",
    "ehdotus": "ehdotus",
    "arvonta": "arvonta",
    "kick": "mod_kick",
    "ban": "mod_ban",
    "mute": "mod_mute",
    "unmute": "mod_unmute",
    "varoitus": "mod_warn",
    "varoitukset": "mod_warn",
    "poista_varoitukset": "mod_warn",
    "clear": "mod_purge",
}


class KomennotListaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _kerää_kaikki_komennot(self):
        """Kerää kaikki puun komennot (päivittyy aina kun puu muuttuu)."""
        rivit = []
        for cmd in self.bot.tree.walk_commands():
            if not getattr(cmd, "name", None):
                continue
            nimi = getattr(cmd, "qualified_name", None) or cmd.name
            kuvaus = getattr(cmd, "description", None) or "–"
            if not kuvaus or kuvaus == "…":
                kuvaus = "–"
            rivit.append((nimi, kuvaus[:80] if kuvaus else "–"))
        return sorted(rivit, key=lambda x: x[0].lower())

    @app_commands.command(name="komennot", description="Näytä kaikki Xevrionin komennot")
    async def komennot(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "komennot_lista")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä tällä palvelimella. Ota se käyttöön web-dashboardista.",
                ephemeral=True
            )
            return
        lista = self._kerää_kaikki_komennot()
        if not lista:
            await interaction.response.send_message("Komentoja ei löytynyt.", ephemeral=True)
            return

        settings = self.bot._db.get_guild_settings(str(interaction.guild_id)) if interaction.guild_id else {}
        def _on_off(cmd_name: str) -> str:
            feat = COMMAND_TO_FEATURE.get(cmd_name)
            if feat is None:
                return "–"
            val = settings.get(feat, True)
            return "🟢 Päällä" if val else "🔴 Pois"

        # Jaetaan useampaan fieldiin (max 1024 merkkiä per field) jotta mobiililla ja PC:llä kaikki näkyy
        CHUNK_LEN = 10
        chunks = [lista[i : i + CHUNK_LEN] for i in range(0, len(lista), CHUNK_LEN)]
        total = len(chunks)
        embed = discord.Embed(
            title="Xevrionin komennot",
            description="Kaikki slash-komennot. 🟢 Päällä / 🔴 Pois = web-dashboard → Yleinen → Komennot.",
            color=discord.Color.blue()
        )
        for idx, chunk in enumerate(chunks, 1):
            lines = [f"**/{nimi}** — {_on_off(nimi)} — {kuvaus}" for nimi, kuvaus in chunk]
            text = "\n".join(lines)
            name = f"Komennot ({idx}/{total})" if total > 1 else "Komennot"
            embed.add_field(name=name, value=text or "–", inline=False)
        embed.set_footer(text="Päällä/Pois: web-dashboard → Yleinen → Komennot")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(KomennotListaCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
