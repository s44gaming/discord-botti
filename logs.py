import discord
from datetime import datetime, timezone


async def send_guild_log(
    bot,
    guild: discord.Guild,
    log_key: str,
    title: str,
    description: str,
    *,
    color: discord.Color | None = None,
):
    """
    Yleinen lokittaja: lähettää embedin palvelimen valittuun logikanavaan,
    jos logityyppi on webissä päällä.
    """
    if not guild:
        return
    try:
        enabled = bot.is_log_enabled(guild.id, log_key)
    except Exception:
        enabled = True
    if not enabled:
        return

    channel_id = None
    try:
        channel_id = bot.get_log_channel(guild.id)
    except Exception:
        channel_id = None
    if not channel_id:
        return

    try:
        channel = await bot.fetch_channel(channel_id)
    except (discord.NotFound, discord.Forbidden):
        return
    if not isinstance(channel, discord.TextChannel):
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color or discord.Color.orange(),
        timestamp=datetime.now(timezone.utc),
    )
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        return

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg

