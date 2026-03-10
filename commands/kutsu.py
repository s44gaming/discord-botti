import discord
from discord import app_commands
from discord.ext import commands
from config import BOT_APPLY_URL, BOT_INVITE_LINK


class KutsuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kutsu", description="Linkki lisätä botti omaan palvelimeen")
    async def kutsu(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "kutsu")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä tällä palvelimella.",
                ephemeral=True
            )
            return
        url = (BOT_APPLY_URL or "").strip()
        if not url:
            await interaction.response.send_message(
                "🔗 Botin kutsulinkkiä ei ole vielä asetettu. Ylläpitäjä voi lisätä sen kehittäjäportaalista (Botin tiedot).",
                ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"🔗 **Lisää botti omaan palvelimeen:**\n{url}",
            ephemeral=True
        )

    @app_commands.command(name="lähetäkutsu", description="Lähettää yhteisön kutsulinkin viestinä kanavalle")
    @app_commands.default_permissions(manage_guild=True)
    async def laheta_kutsu(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "kutsuviesti")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä tällä palvelimella.",
                ephemeral=True
            )
            return
        url = (BOT_INVITE_LINK or "").strip()
        if not url:
            await interaction.response.send_message(
                "🔗 Yhteisön kutsulinkkiä ei ole asetettu. Aseta se kehittäjäportaalin Botin tiedot -osiosta.",
                ephemeral=True
            )
            return
        await interaction.response.send_message("Viesti lähetetty.", ephemeral=True)
        await interaction.channel.send(f"**Botin viralliseen Yhteisön kutsu:** {url}")


async def setup(bot):
    await bot.add_cog(KutsuCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
