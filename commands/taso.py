"""Levellijärjestelmän /taso-komento."""
import discord
from discord import app_commands
from discord.ext import commands
import database


def _xp_for_next_level(level: int) -> int:
    """XP määrä seuraavaan tasoon (nykyisen tason jälkeen)."""
    return 100 * (level + 1)


def _xp_progress_in_level(xp: int) -> tuple[int, int, int]:
    """Palauttaa (current_in_level, needed_for_level, level)."""
    level = database._xp_to_level(xp)
    xp_at_level_start = 100 * level * (level + 1) // 2 if level > 0 else 0
    xp_needed = _xp_for_next_level(level)
    current = xp - xp_at_level_start
    return current, xp_needed, level


class TasoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="taso", description="Näytä taso ja XP")
    @app_commands.describe(käyttäjä="Käyttäjä (valinnainen, oletuksena itse)")
    async def taso(self, interaction: discord.Interaction, käyttäjä: discord.Member | None = None):
        if not interaction.guild:
            return await interaction.response.send_message("Vain palvelimella.", ephemeral=True)
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "taso")
        if not enabled:
            return await interaction.response.send_message(
                "⚠️ Levellijärjestelmä on poissa käytöstä tällä palvelimella.",
                ephemeral=True,
            )
        target = käyttäjä or (interaction.user if isinstance(interaction.user, discord.Member) else None)
        if not target:
            return await interaction.response.send_message("Käyttäjää ei löydy.", ephemeral=True)
        xp, level = database.get_user_xp(str(interaction.guild_id), str(target.id))
        current, needed, _ = _xp_progress_in_level(xp)
        bar_len = 10
        filled = int(bar_len * current / needed) if needed else bar_len
        bar = "█" * filled + "░" * (bar_len - filled)
        embed = discord.Embed(
            title=f"Taso: {target.display_name}",
            description=f"**Taso {level}** • {xp} XP\n`{bar}` {current}/{needed} XP seuraavaan",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Jatka viestien kirjoittamista saadaksesi lisää XP:tä!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tasonboard", description="Näytä tasoTOP-10")
    async def tasonboard(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Vain palvelimella.", ephemeral=True)
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "tasonboard")
        if not enabled:
            return await interaction.response.send_message(
                "⚠️ Levellijärjestelmä on poissa käytöstä tällä palvelimella.",
                ephemeral=True,
            )
        rows = database.get_leaderboard(str(interaction.guild_id), 10)
        if not rows:
            return await interaction.response.send_message(
                "Ei vielä XP-dataa. Kirjoita viestejä!",
                ephemeral=True,
            )
        lines = []
        for i, (uid, xp, lvl) in enumerate(rows, 1):
            user = interaction.guild.get_member(int(uid))
            name = user.display_name if user else f"<@{uid}>"
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"`{i}.`")
            lines.append(f"{medal} **{name}** — Taso {lvl} ({xp} XP)")
        embed = discord.Embed(
            title="Tasonboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TasoCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
