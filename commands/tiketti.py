"""
Tikettijärjestelmä. Staff-rooli, kategoria ja kanava määritetään web-dashboardista.
"""
import discord
from discord import app_commands
from discord.ext import commands
import database


def _error(msg: str) -> discord.Embed:
    return discord.Embed(color=discord.Color.red(), description=f"❌ {msg}")


class TicketOpenButton(discord.ui.Button):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.primary, label="Avaa tiketti", custom_id="ticket_open")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "Tikettejä voi avata vain palvelimella.", ephemeral=True
            )
        if not await self.bot.is_feature_enabled(interaction.guild_id, "tiketti"):
            return await interaction.response.send_message(
                "Tikettijärjestelmä on poissa käytöstä.", ephemeral=True
            )
        settings = self.bot.get_ticket_settings(interaction.guild_id)
        ch_id = settings.get("channel_id")
        cat_id = settings.get("category_id")
        role_id = settings.get("staff_role_id")
        if not ch_id or not cat_id or not role_id:
            return await interaction.response.send_message(
                "Tiketti-asetukset puuttuvat. Aseta web-dashboardista rooli, kategoria ja kanava.",
                ephemeral=True
            )
        ch_str = str(ch_id)
        if str(interaction.channel_id) != ch_str:
            return await interaction.response.send_message(
                f"Avaa tiketti kanavalla <#{ch_str}>.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        category = interaction.guild.get_channel(int(cat_id))
        if not category or not isinstance(category, discord.CategoryChannel):
            return await interaction.followup.send(
                "Tiketin kategoriaa ei löydy.", ephemeral=True
            )

        staff_role = interaction.guild.get_role(int(role_id))
        if not staff_role:
            return await interaction.followup.send(
                "Staff-roolia ei löydy.", ephemeral=True
            )

        safe_name = "".join(c if c.isalnum() or c in "-_" else "" for c in interaction.user.display_name)[:12] or "user"
        name = f"tiketti-{safe_name}-{interaction.user.id % 10000}"
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }

        try:
            channel = await interaction.guild.create_text_channel(
                name=name,
                category=category,
                overwrites=overwrites,
            )
        except discord.Forbidden:
            return await interaction.followup.send("Ei oikeuksia luoda kanavia.", ephemeral=True)

        embed = discord.Embed(
            title="Tiketti avattu",
            description=f"Tervetuloa {interaction.user.mention}! Kuvatko ongelma tai kysymyksesi alle.\nStaff vastaa pian.",
            color=discord.Color.green(),
        )
        close_view = TicketCloseView(self.bot)
        await channel.send(content=interaction.user.mention, embed=embed, view=close_view)
        await interaction.followup.send(f"Tiketti avattu: {channel.mention}", ephemeral=True)


class TicketOpenView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TicketOpenButton(bot))


class TicketCloseButton(discord.ui.Button):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.danger, label="Sulje tiketti", custom_id="ticket_close")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return
        settings = self.bot.get_ticket_settings(interaction.guild_id)
        role_id = settings.get("staff_role_id")
        if not role_id:
            return await interaction.response.send_message("Staff-roolia ei määritetty.", ephemeral=True)
        staff_role = interaction.guild.get_role(int(role_id))
        if not staff_role or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Et voi sulkea tätä tiketin.", ephemeral=True)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Vain staff voi sulkea tiketin.", ephemeral=True)
        await interaction.response.send_message("Tiketti suljetaan...", ephemeral=True)
        try:
            await interaction.channel.delete(reason=f"Tiketti suljettu: {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send("Ei oikeuksia poistaa kanavaa.", ephemeral=True)


class TicketCloseView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TicketCloseButton(bot))


class TikettiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tiketti_paneeli", description="Lähettää tiketti-paneelin webissä valitulle kanavalle")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Vain palvelimella.", ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Vain ylläpitäjät voivat käyttää.", ephemeral=True)
        if not await self.bot.is_feature_enabled(interaction.guild_id, "tiketti"):
            return await interaction.response.send_message(
                "Tikettijärjestelmä on poissa käytöstä (web-dashboard).", ephemeral=True
            )
        settings = self.bot.get_ticket_settings(interaction.guild_id)
        ch_id = settings.get("channel_id")
        if not ch_id or not settings.get("category_id") or not settings.get("staff_role_id"):
            return await interaction.response.send_message(
                "Aseta web-dashboardista: staff-rooli, kategoria ja kanava.",
                ephemeral=True
            )

        try:
            target_channel = await self.bot.fetch_channel(int(ch_id))
        except (discord.NotFound, discord.Forbidden):
            return await interaction.response.send_message(
                "Tiketti-kanavaa ei löydy. Tarkista web-asetukset.",
                ephemeral=True
            )
        if not isinstance(target_channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Valittu kanava ei ole tekstikanava.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="Tarvitsetko apua?",
            description="Paina alla olevaa nappia avataksesi tiketin. Staff vastaa mahdollisimman pian.",
            color=discord.Color.blue(),
        )
        view = TicketOpenView(self.bot)
        await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"Tiketti-paneeli lähetetty kanavalle {target_channel.mention}.",
            ephemeral=True
        )


async def setup(bot):
    bot.add_view(TicketOpenView(bot))
    bot.add_view(TicketCloseView(bot))
    await bot.add_cog(TikettiCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
