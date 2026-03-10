import discord
from discord import app_commands
from discord.ext import commands


class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Näytä palvelimen tiedot")
    async def info(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "info")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä tällä palvelimella.",
                ephemeral=True
            )
            return
        guild = interaction.guild
        embed = discord.Embed(title=guild.name, color=discord.Color.blue())
        embed.add_field(name="Jäseniä", value=str(guild.member_count), inline=True)
        embed.add_field(name="Kanavia", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Luotu", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(InfoCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
