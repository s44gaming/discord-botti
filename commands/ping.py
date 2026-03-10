import discord
from discord import app_commands
from discord.ext import commands


class PingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Tarkista botin vastausaika")
    async def ping(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "ping")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä tällä palvelimella. Ota se käyttöön web-dashboardista.",
                ephemeral=True
            )
            return
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")


async def setup(bot):
    await bot.add_cog(PingCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
