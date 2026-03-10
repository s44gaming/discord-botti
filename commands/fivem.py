"""
FiveM-palvelimen tila. Asetukset web-dashboardista (host + port).
"""
import discord
from discord import app_commands
from discord.ext import commands
import fivem_status


class FivemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fivem", description="Näytä FiveM-palvelimen tila (asetukset webistä)")
    @app_commands.describe(lähetä_kanavalle="Lähetä status asetettuun kanavalle (vaatii palvelimen hallinnan)")
    async def fivem(self, interaction: discord.Interaction, lähetä_kanavalle: bool = False):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "fivem")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ FiveM-tila on poistettu käytöstä tällä palvelimella. Ota se käyttöön web-dashboardista.",
                ephemeral=True
            )
            return
        settings = self.bot.get_fivem_settings(interaction.guild_id)
        host, port = settings.get("host", ""), settings.get("port", "30120")
        if not host:
            await interaction.response.send_message(
                "❌ FiveM-palvelinta ei ole asetettu. Aseta palvelimen osoite ja portti web-dashboardista (Palvelimen asetukset → FiveM).",
                ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        result = fivem_status.fetch_fivem_status(host, port)
        if result is None:
            await interaction.followup.send("❌ Palvelimen tietoja ei saatu.", ephemeral=True)
            return
        if not result.get("online"):
            await interaction.followup.send(
                f"❌ **FiveM-palvelin** ({host}:{port})\n{result.get('error', 'Ei yhteyttä.')}",
                ephemeral=True
            )
            return
        hostname = result.get("hostname", "FiveM")
        players = result.get("players", 0)
        max_p = result.get("max", 48)
        map_name = result.get("map", "–")
        embed = discord.Embed(
            title=f"🎮 {hostname}",
            description=f"**{host}:{port}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Pelaajia", value=f"{players} / {max_p}", inline=True)
        embed.add_field(name="Kartta", value=map_name, inline=True)

        channel_id = settings.get("channel_id")
        if lähetä_kanavalle and channel_id and interaction.user.guild_permissions.manage_guild:
            channel = interaction.guild.get_channel(int(channel_id))
            if channel:
                try:
                    await channel.send(embed=embed)
                    await interaction.followup.send(f"✅ Status lähetetty kanavalle {channel.mention}", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send("❌ Ei oikeutta lähettää viestejä kyseiselle kanavalle.", ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(f"❌ Virhe: {e}", ephemeral=True)
            else:
                await interaction.followup.send("❌ Kanavaa ei löydy. Tarkista asetukset webistä.", ephemeral=True)
        else:
            msg = "ℹ️ Aseta status-kanava web-dashboardista (FiveM-asetukset), jotta voit lähettää sinne valinnalla »Lähetä kanavalle«." if lähetä_kanavalle and not channel_id else None
            await interaction.followup.send(embed=embed, ephemeral=True)
            if msg:
                await interaction.followup.send(msg, ephemeral=True)


async def setup(bot):
    await bot.add_cog(FivemCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
