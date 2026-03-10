import discord
from collections import deque
from logs import send_guild_log

# Estetään saman poiston lokitus kahdesti (Discord voi joskus lähettää eventin kahdesti)
_LOGGED_DELETES: set[tuple[int, int]] = set()
_LOGGED_DELETES_DEQUE: deque[tuple[int, int]] = deque()


async def setup(bot):
    async def on_member_join(member: discord.Member):
        await send_guild_log(
            bot,
            member.guild,
            "member_join",
            "Jäsen liittyi",
            f"**Jäsen:** {member} (`{member.id}`)\n**Tili luotu:** {member.created_at.strftime('%d.%m.%Y %H:%M')}",
            color=discord.Color.green(),
        )
        # Tervetuloa-viesti jos asetuksissa päällä
        try:
            welcome = bot.get_welcome_settings(member.guild.id)
            if welcome.get("enabled") and welcome.get("channel_id"):
                channel = await bot.fetch_channel(welcome["channel_id"])
                if isinstance(channel, discord.TextChannel):
                    await channel.send(f"Tervetuloa {member.mention} palvelimelle! 👋")
        except (discord.NotFound, discord.Forbidden, AttributeError):
            pass

    async def on_member_remove(member: discord.Member):
        await send_guild_log(
            bot,
            member.guild,
            "member_leave",
            "Jäsen poistui",
            f"**Jäsen:** {member} (`{member.id}`)",
            color=discord.Color.red(),
        )

    async def on_message_delete(message: discord.Message):
        if not message.guild:
            return
        key = (message.guild.id, message.id)
        if key in _LOGGED_DELETES:
            return
        if len(_LOGGED_DELETES_DEQUE) >= 500:
            old = _LOGGED_DELETES_DEQUE.popleft()
            _LOGGED_DELETES.discard(old)
        _LOGGED_DELETES.add(key)
        _LOGGED_DELETES_DEQUE.append(key)
        author = message.author
        content = (message.content or "").strip()
        content_line = f"\n**Sisältö:** {content[:900]}" if content else ""
        await send_guild_log(
            bot,
            message.guild,
            "message_delete",
            "Viesti poistettu",
            f"**Kanava:** <#{message.channel.id}>\n**Kirjoittaja:** {author} (`{author.id}`){content_line}",
            color=discord.Color.orange(),
        )

    async def on_message_edit(before: discord.Message, after: discord.Message):
        if not after.guild:
            return
        if before.content == after.content:
            return
        b = (before.content or "").strip()
        a = (after.content or "").strip()
        await send_guild_log(
            bot,
            after.guild,
            "message_edit",
            "Viesti muokattu",
            f"**Kanava:** <#{after.channel.id}>\n**Kirjoittaja:** {after.author} (`{after.author.id}`)\n**Ennen:** {b[:450] or '—'}\n**Jälkeen:** {a[:450] or '—'}",
            color=discord.Color.blurple(),
        )

    bot.add_listener(on_member_join, "on_member_join")
    bot.add_listener(on_member_remove, "on_member_remove")
    bot.add_listener(on_message_delete, "on_message_delete")
    bot.add_listener(on_message_edit, "on_message_edit")

