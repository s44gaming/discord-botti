"""
Moderaatiokomennot.
Moderaattoriroolit + toimintojen kytkimet + logikanava hallitaan web-dashboardista (palvelinkohtaisesti).
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

import database
from logs import send_guild_log


def _error(msg: str) -> discord.Embed:
    return discord.Embed(color=discord.Color.red(), description=f"❌ {msg}")


def _ok(msg: str) -> discord.Embed:
    return discord.Embed(color=discord.Color.green(), description=f"✅ {msg}")


class ModeraatioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _check_mod(self, interaction: discord.Interaction, action: str) -> bool:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return False
        if not self.bot.has_mod_permission(interaction.user):
            await interaction.response.send_message(embed=_error("Sinulla ei ole moderaattorioikeuksia."), ephemeral=True)
            return False
        if not self.bot.is_mod_action_enabled(interaction.guild_id, action):
            await interaction.response.send_message(
                embed=_error("Toiminto on poistettu käytöstä tällä palvelimella (web-dashboard)."),
                ephemeral=True,
            )
            return False
        return True

    @app_commands.command(name="kick", description="Potkaisee jäsenen palvelimelta")
    @app_commands.describe(jäsen="Potkaistava jäsen", syy="Syy (valinnainen)")
    async def kick(self, interaction: discord.Interaction, jäsen: discord.Member, syy: str = ""):
        if not await self._check_mod(interaction, "kick"):
            return
        if jäsen.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=_error("Et voi potkaista jäsentä, jolla on sama/korkeampi rooli."), ephemeral=True)
            return
        try:
            await jäsen.kick(reason=syy or f"Moderaattori: {interaction.user}")
            await interaction.response.send_message(embed=_ok(f"Potkaistu: {jäsen}"))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderaatio: Kick",
                f"**Kohde:** {jäsen} (`{jäsen.id}`)\n**Moderaattori:** {interaction.user}\n**Syy:** {syy or 'Ei syytä'}",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("Ei oikeuksia potkaista."), ephemeral=True)

    @app_commands.command(name="ban", description="Estää jäsenen palvelimelta")
    @app_commands.describe(jäsen="Estettävä jäsen", syy="Syy (valinnainen)", viestit="Poistettavat viestit (0–7 päivää)")
    async def ban(self, interaction: discord.Interaction, jäsen: discord.Member, syy: str = "", viestit: int = 0):
        if not await self._check_mod(interaction, "ban"):
            return
        if jäsen.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=_error("Et voi estää jäsentä, jolla on sama/korkeampi rooli."), ephemeral=True)
            return
        delete_days = max(0, min(7, viestit))
        delete_seconds = delete_days * 86400 if delete_days else 0
        try:
            await jäsen.ban(reason=syy or f"Moderaattori: {interaction.user}", delete_message_seconds=delete_seconds)
            await interaction.response.send_message(embed=_ok(f"Estetty: {jäsen}"))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderaatio: Ban",
                f"**Kohde:** {jäsen} (`{jäsen.id}`)\n**Moderaattori:** {interaction.user}\n**Syy:** {syy or 'Ei syytä'}\n**Viestien poisto:** {delete_days} päivää",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("Ei oikeuksia estää."), ephemeral=True)

    @app_commands.command(name="mute", description="Asettaa jäsenen mykistykseen (timeout)")
    @app_commands.describe(jäsen="Mykistettävä jäsen", minuutit="Kesto minuutteina (1–40320)", syy="Syy (valinnainen)")
    async def mute(self, interaction: discord.Interaction, jäsen: discord.Member, minuutit: int = 60, syy: str = ""):
        if not await self._check_mod(interaction, "mute"):
            return
        duration = max(1, min(40320, minuutit))
        until = datetime.now(timezone.utc) + timedelta(minutes=duration)
        try:
            await jäsen.timeout(until, reason=syy or f"Moderaattori: {interaction.user}")
            await interaction.response.send_message(embed=_ok(f"Mykistetty {jäsen} {duration} minuutiksi."))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderaatio: Mute (timeout)",
                f"**Kohde:** {jäsen} (`{jäsen.id}`)\n**Moderaattori:** {interaction.user}\n**Kesto:** {duration} min\n**Syy:** {syy or 'Ei syytä'}",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("Ei oikeuksia mykistää."), ephemeral=True)

    @app_commands.command(name="unmute", description="Poistaa jäsenen mykistyksen")
    @app_commands.describe(jäsen="Mykistyksen poistettava jäsen")
    async def unmute(self, interaction: discord.Interaction, jäsen: discord.Member):
        if not await self._check_mod(interaction, "unmute"):
            return
        try:
            await jäsen.timeout(None, reason=f"Moderaattori: {interaction.user}")
            await interaction.response.send_message(embed=_ok(f"Mykistys poistettu: {jäsen}"))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderaatio: Unmute",
                f"**Kohde:** {jäsen} (`{jäsen.id}`)\n**Moderaattori:** {interaction.user}",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("Ei oikeuksia poistaa mykistystä."), ephemeral=True)

    @app_commands.command(name="varoitus", description="Anna varoitus jäsenelle")
    @app_commands.describe(jäsen="Jäsen", syy="Syy (valinnainen)")
    async def varoitus(self, interaction: discord.Interaction, jäsen: discord.Member, syy: str = ""):
        if not await self._check_mod(interaction, "warn"):
            return
        database.add_warn(str(interaction.guild_id), str(jäsen.id), str(interaction.user.id), syy)
        total = len(database.get_user_warns(str(interaction.guild_id), str(jäsen.id)))
        await interaction.response.send_message(embed=_ok(f"Varoitus annettu: {jäsen}. Varoituksia yhteensä: {total}"))
        await send_guild_log(
            self.bot,
            interaction.guild,
            "mod_actions",
            "Moderaatio: Varoitus",
            f"**Kohde:** {jäsen} (`{jäsen.id}`)\n**Moderaattori:** {interaction.user}\n**Syy:** {syy or 'Ei syytä'}\n**Varoituksia nyt:** {total}",
            color=discord.Color.orange(),
        )

    @app_commands.command(name="varoitukset", description="Näytä jäsenen varoitukset")
    @app_commands.describe(jäsen="Jäsen")
    async def varoitukset(self, interaction: discord.Interaction, jäsen: discord.Member):
        if not await self._check_mod(interaction, "warn"):
            return
        warns = database.get_user_warns(str(interaction.guild_id), str(jäsen.id))
        if not warns:
            await interaction.response.send_message(embed=discord.Embed(color=discord.Color.blue(), description=f"{jäsen} ei ole saanut varoituksia."))
            return
        lines = []
        for i, w in enumerate(warns[:10], 1):
            ts = (w.get("created_at") or "")[:16] or "—"
            lines.append(f"**{i}.** {ts} – {w.get('reason','')[:80]}")
        embed = discord.Embed(
            title=f"Varoitukset: {jäsen}",
            description="\n".join(lines) + (f"\n\n_+{len(warns)-10} lisää_" if len(warns) > 10 else ""),
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Yhteensä {len(warns)} varoitusta")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="poista_varoitukset", description="Poista kaikki varoitukset jäseneltä")
    @app_commands.describe(jäsen="Jäsen")
    async def poista_varoitukset(self, interaction: discord.Interaction, jäsen: discord.Member):
        if not await self._check_mod(interaction, "warn"):
            return
        n = database.clear_warns(str(interaction.guild_id), str(jäsen.id))
        await interaction.response.send_message(embed=_ok(f"Poistettu {n} varoitusta käyttäjältä {jäsen}."))
        if n:
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderaatio: Varoitusten poisto",
                f"**Kohde:** {jäsen} (`{jäsen.id}`)\n**Moderaattori:** {interaction.user}\n**Poistettu:** {n} varoitusta",
                color=discord.Color.orange(),
            )

    @app_commands.command(name="purge", description="Poistaa viestejä kanavalta")
    @app_commands.describe(määrä="Poistettavien viestien määrä (1–100)", käyttäjä="Rajaa tietyn käyttäjän viesteihin (valinnainen)")
    async def purge(self, interaction: discord.Interaction, määrä: int, käyttäjä: discord.Member | None = None):
        if not await self._check_mod(interaction, "purge"):
            return
        amount = max(1, min(100, määrä))

        def check(msg: discord.Message) -> bool:
            return (msg.author.id == käyttäjä.id) if käyttäjä else True

        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            await interaction.response.send_message(embed=_ok(f"Poistettu {len(deleted)} viestiä."), ephemeral=True)
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderaatio: Purge",
                f"**Moderaattori:** {interaction.user}\n**Kanava:** <#{interaction.channel.id}>\n**Poistettu:** {len(deleted)} viestiä",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("Ei oikeutta poistaa viestejä."), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ModeraatioCog(bot))