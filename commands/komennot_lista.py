"""
Näyttää kaikki käytettävissä olevat slash-komennot. Päivittyy automaattisesti kun komentoja lisätään.
"""
import discord
from discord import app_commands
from discord.ext import commands


class KomennotListaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _kerää_kaikki_komennot(self):
        """Kerää kaikki puun komennot (päivittyy aina kun puu muuttuu)."""
        rivit = []
        for cmd in self.bot.tree.walk_commands():
            if not getattr(cmd, "name", None):
                continue
            # qualified_name = "ryhmä alikomento" tai vain "komento"
            nimi = getattr(cmd, "qualified_name", None) or cmd.name
            kuvaus = getattr(cmd, "description", None) or "–"
            if not kuvaus or kuvaus == "…":
                kuvaus = "–"
            rivit.append((f"/{nimi}", kuvaus))
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
        # Embed max 25 fieldiä, joten jaetaan osiin tai yksi kuvaus
        text = "\n".join(f"**{nimi}** — {kuvaus[:80]}" for nimi, kuvaus in lista)
        if len(text) > 3900:
            text = text[:3890] + "\n…"
        embed = discord.Embed(
            title="Xevrionin komennot",
            description="Kaikki käytettävissä olevat slash-komennot. Lista päivittyy automaattisesti uusien komentojen tullessa.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Komennot", value=text or "–", inline=False)
        embed.set_footer(text="Osa komennoista voi olla pois päältä tällä palvelimella (asetukset webistä).")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(KomennotListaCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
