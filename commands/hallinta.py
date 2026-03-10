import discord
from discord import app_commands
from discord.ext import commands
from config import BASE_URL


class HallintaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hallinta", description="Linkki web-hallintapaneeliin")
    async def hallinta(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "hallinta")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä.",
                ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"🌐 Hallinnoi bottia: {BASE_URL}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(HallintaCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
