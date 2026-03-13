"""
Palvelimen tilastokanavat (SERVER STATS): Jäsenet, Ihmiset, Online, Offline.
Luodaan ääni-/näyttökanavat ja päivitetään ne säännöllisesti.
Rate limit -suoja: cooldown per guild, viive kanavien välillä.
"""
import asyncio
import time
import discord
import database

# Discord rate limit: PATCH channels voi aiheuttaa 429 (~5 min odotus). Vältetään.
UPDATE_INTERVAL = 300  # minuuttia, taustasilmukka
STARTUP_DELAY = 330  # sekuntia ennen ensimmäistä päivitystä (rate limit -palautuminen)
PRESENCE_DEBOUNCE = 60  # sekuntia, presence-spammin debounce
GUILD_UPDATE_COOLDOWN = 330  # sekuntia, minimiväli saman guildin päivityksille
CHANNEL_EDIT_DELAY = 3  # sekuntia kanavamuutosten väliin
_pending_presence_tasks = {}
_last_update_time = {}
_first_allowed_time = 0  # ei kanavamuutoksia ennen tätä (monotonic)


async def _get_counts(guild: discord.Guild) -> dict:
    """Laskee tilastot: members, humans, online, offline."""
    total = guild.member_count or 0
    try:
        if guild.member_count == 0 and guild.large:
            await guild.chunk()
    except Exception:
        pass

    humans = 0
    online = 0
    for m in guild.members:
        if not m.bot:
            humans += 1
        if m.status != discord.Status.offline and m.status != discord.Status.invisible:
            online += 1

    # Jos presence-data ei ole saatavilla, käytä arviota
    if online == 0 and total > 0 and hasattr(guild, "approximate_presence_count") and guild.approximate_presence_count:
        online = guild.approximate_presence_count
    offline = max(0, total - online)

    return {
        "members": total,
        "humans": humans,
        "online": online,
        "offline": offline,
    }


def _format_name(stat_key: str, count: int, labels: dict) -> str:
    """Muodostaa kanavan nimen, esim. 'Jäsenet: 37'. labels tulee tietokannasta."""
    label = (labels or {}).get(stat_key) or stat_key.capitalize()
    return f"{label}: {count}"


def _can_update_guild(guild_id: int) -> bool:
    """Tarkista onko guild cooldownissa ja onko startup-viive ohi (rate limit -suoja)."""
    now = time.monotonic()
    if now < _first_allowed_time:
        return False
    last = _last_update_time.get(guild_id, 0)
    if last > 0 and (now - last) < GUILD_UPDATE_COOLDOWN:
        return False
    _last_update_time[guild_id] = now
    return True


async def _update_or_create_channels(bot, guild: discord.Guild, settings: dict, counts: dict, skip_cooldown: bool = False) -> None:
    """Luo tai päivittää tilastokanavat."""
    if not skip_cooldown and not _can_update_guild(guild.id):
        return
    if not guild.me.guild_permissions.manage_channels:
        return

    category_id = settings.get("category_id")
    category_name = settings.get("category_name") or "SERVER STATS"
    stats = settings.get("stats") or ["members", "humans", "online", "offline"]
    channel_ids = settings.get("channel_ids") or {}
    if not isinstance(channel_ids, dict):
        channel_ids = {}

    category = None
    if category_id:
        category = guild.get_channel(int(category_id))

    if not category:
        try:
            category = await guild.create_category(name=category_name)
            database.set_server_stats_settings(guild.id, category_id=str(category.id))
            channel_ids = {}
        except discord.Forbidden:
            return
        except Exception:
            return

    labels = settings.get("labels") or {}
    for stat_key in stats:
        count = counts.get(stat_key, 0)
        new_name = _format_name(stat_key, count, labels)

        ch_id = channel_ids.get(stat_key)
        channel = guild.get_channel(int(ch_id)) if ch_id else None

        if not channel:
            try:
                channel = await guild.create_voice_channel(
                    name=new_name,
                    category=category,
                    user_limit=0,
                )
                channel_ids[stat_key] = str(channel.id)
                await asyncio.sleep(CHANNEL_EDIT_DELAY)
            except discord.Forbidden:
                continue
            except Exception:
                continue
        else:
            if channel.name != new_name:
                try:
                    await channel.edit(name=new_name)
                    await asyncio.sleep(CHANNEL_EDIT_DELAY)
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

    if channel_ids:
        database.set_server_stats_settings(guild.id, channel_ids=channel_ids)


async def _update_all_server_stats(bot):
    """Päivittää kaikkien palvelimien tilastokanavat. Säilyttää cooldownin."""
    for guild in bot.guilds:
        settings = database.get_server_stats_settings(str(guild.id))
        if not settings.get("enabled"):
            continue
        try:
            counts = await _get_counts(guild)
            await _update_or_create_channels(bot, guild, settings, counts)
            await asyncio.sleep(CHANNEL_EDIT_DELAY * 2)
        except Exception:
            pass


def _set_startup_delay():
    global _first_allowed_time
    _first_allowed_time = time.monotonic() + STARTUP_DELAY


async def _server_stats_loop(bot):
    """Taustasilmukka: päivittää tilastot säännöllisesti."""
    await bot.wait_until_ready()
    _set_startup_delay()
    await asyncio.sleep(STARTUP_DELAY)
    while not bot.is_closed():
        try:
            await _update_all_server_stats(bot)
        except Exception:
            pass
        await asyncio.sleep(UPDATE_INTERVAL)


async def update_guild_server_stats_now(bot, guild_id: int) -> bool:
    """Päivittää yhden palvelimen tilastokanavat heti. Palauttaa True jos onnistui."""
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return False
    settings = database.get_server_stats_settings(str(guild_id))
    if not settings.get("enabled"):
        return False
    try:
        counts = await _get_counts(guild)
        await _update_or_create_channels(bot, guild, settings, counts, skip_cooldown=True)
        return True
    except Exception:
        return False


def _schedule_immediate_update(bot, guild_id: int, debounce: bool = False):
    """Ajoittaa välitön päivitys. debounce=True: peruuttaa edellisen odottavan (presence-spammin välttämiseksi)."""
    async def _do():
        await asyncio.sleep(3 if not debounce else PRESENCE_DEBOUNCE)
        if debounce and guild_id in _pending_presence_tasks:
            _pending_presence_tasks.pop(guild_id, None)
        guild = bot.get_guild(guild_id)
        if not guild:
            return
        settings = database.get_server_stats_settings(str(guild_id))
        if not settings.get("enabled"):
            return
        try:
            counts = await _get_counts(guild)
            await _update_or_create_channels(bot, guild, settings, counts)
        except Exception:
            pass

    if debounce:
        old = _pending_presence_tasks.pop(guild_id, None)
        if old and not old.done():
            old.cancel()
        _pending_presence_tasks[guild_id] = asyncio.create_task(_do())
    else:
        asyncio.create_task(_do())


async def setup(bot):
    asyncio.create_task(_server_stats_loop(bot))

    async def on_member_join(member: discord.Member):
        _schedule_immediate_update(bot, member.guild.id)

    async def on_member_remove(member: discord.Member):
        _schedule_immediate_update(bot, member.guild.id)

    def _presence_affects_online_count(before_status, after_status):
        off = (discord.Status.offline, discord.Status.invisible)
        b_off = before_status in off if before_status else True
        a_off = after_status in off if after_status else True
        return b_off != a_off  # offline↔online muutos

    async def on_presence_update(before, after):
        if not (before and after and getattr(after, "guild", None)):
            return
        before_status = getattr(before, "status", None)
        after_status = getattr(after, "status", None)
        if before_status != after_status and _presence_affects_online_count(before_status, after_status):
            _schedule_immediate_update(bot, after.guild.id, debounce=True)

    bot.add_listener(on_member_join, "on_member_join")
    bot.add_listener(on_member_remove, "on_member_remove")
    bot.add_listener(on_presence_update, "on_presence_update")
