"""Levellijärjestelmä: XP viesteistä ja taso-ilmoitukset."""
import discord
import time

_XP_COOLDOWNS: dict[tuple[int, int], float] = {}
_VOICE_JOIN: dict[tuple[int, int], tuple[int, float]] = {}  # (guild_id, user_id) -> (channel_id, join_time)
_MAX_COOLDOWNS = 5000


def _prune_cooldowns():
    global _XP_COOLDOWNS
    if len(_XP_COOLDOWNS) > _MAX_COOLDOWNS:
        now = time.monotonic()
        _XP_COOLDOWNS = {k: v for k, v in _XP_COOLDOWNS.items() if now - v < 600}


async def setup(bot):
    async def on_message(message: discord.Message):
        if not message.guild or message.author.bot:
            return
        try:
            settings = bot.get_level_settings(message.guild.id)
        except AttributeError:
            return
        if not settings.get("enabled"):
            return
        text_no_xp = set(settings.get("text_no_xp_channel_ids") or [])
        if str(message.channel.id) in text_no_xp:
            return
        xp_per = settings.get("xp_per_message", 15)
        cooldown_sec = settings.get("xp_cooldown", 60)
        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        last = _XP_COOLDOWNS.get(key, 0)
        if now - last < cooldown_sec:
            return
        _XP_COOLDOWNS[key] = now
        _prune_cooldowns()
        new_xp, new_level, level_up = bot._db.add_user_xp(
            str(message.guild.id), str(message.author.id), xp_per
        )
        if level_up and new_level > 0:
            if settings.get("channel_id"):
                try:
                    ch = await bot.fetch_channel(settings["channel_id"])
                    if isinstance(ch, discord.TextChannel):
                        await ch.send(
                            f"🎉 Onnea {message.author.mention}! Olet nyt tasolla **{new_level}**!"
                        )
                except (discord.NotFound, discord.Forbidden):
                    pass
            # Anna tason rooli jos määritelty
            level_roles = settings.get("level_roles") or {}
            role_id = level_roles.get(str(new_level))
            if role_id and isinstance(message.author, discord.Member):
                try:
                    role = message.guild.get_role(int(role_id))
                    if role and role not in message.author.roles:
                        await message.author.add_roles(role, reason=f"Taso {new_level} saavutettu")
                except (discord.Forbidden, discord.HTTPException, ValueError):
                    pass

    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot or not member.guild:
            return
        try:
            settings = bot.get_level_settings(member.guild.id)
        except AttributeError:
            return
        if not settings.get("enabled") or not settings.get("voice_xp_enabled"):
            return
        voice_no_xp = set(settings.get("voice_no_xp_channel_ids") or [])
        xp_per_min = settings.get("voice_xp_per_minute", 10)
        key = (member.guild.id, member.id)
        if before.channel and not after.channel:
            if key in _VOICE_JOIN:
                ch_id, join_time = _VOICE_JOIN.pop(key)
                if str(ch_id) not in voice_no_xp:
                    minutes = max(0, (time.monotonic() - join_time) / 60)
                    xp = int(minutes * xp_per_min)
                    if xp > 0:
                        new_xp, new_level, level_up = bot._db.add_user_xp(
                            str(member.guild.id), str(member.id), xp
                        )
                        if level_up and new_level > 0:
                            if settings.get("channel_id"):
                                try:
                                    ch = await bot.fetch_channel(settings["channel_id"])
                                    if isinstance(ch, discord.TextChannel):
                                        await ch.send(
                                            f"🎉 Onnea {member.mention}! Olet nyt tasolla **{new_level}**!"
                                        )
                                except (discord.NotFound, discord.Forbidden):
                                    pass
                            level_roles = settings.get("level_roles") or {}
                            role_id = level_roles.get(str(new_level))
                            if role_id:
                                try:
                                    role = member.guild.get_role(int(role_id))
                                    if role and role not in member.roles:
                                        await member.add_roles(role, reason=f"Taso {new_level} saavutettu")
                                except (discord.Forbidden, discord.HTTPException, ValueError):
                                    pass
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            if key in _VOICE_JOIN:
                ch_id, join_time = _VOICE_JOIN.pop(key)
                if str(ch_id) not in voice_no_xp:
                    minutes = max(0, (time.monotonic() - join_time) / 60)
                    xp = int(minutes * xp_per_min)
                    if xp > 0:
                        bot._db.add_user_xp(str(member.guild.id), str(member.id), xp)
            if str(after.channel.id) not in voice_no_xp:
                _VOICE_JOIN[key] = (after.channel.id, time.monotonic())
        elif after.channel and str(after.channel.id) not in voice_no_xp:
            _VOICE_JOIN[key] = (after.channel.id, time.monotonic())
        elif not after.channel:
            _VOICE_JOIN.pop(key, None)

    bot.add_listener(on_message, "on_message")
    bot.add_listener(on_voice_state_update, "on_voice_state_update")

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
