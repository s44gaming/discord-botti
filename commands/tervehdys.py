import discord
from discord import app_commands
from discord.ext import commands


class TervehdysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tervehdys", description="Tervehdi käyttäjää")
    async def tervehdys(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "tervehdys")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä tällä palvelimella.",
                ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"Hei {interaction.user.mention}! 👋"
        )


async def setup(bot):
    await bot.add_cog(TervehdysCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
