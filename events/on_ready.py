async def setup(bot):
    async def on_ready_handler():
        print(f"Botti kirjautunut: {bot.user} ({bot.user.id})")
        print(f"Palvelimia: {len(bot.guilds)}")
        await bot.update_presence()

    async def on_guild_join_handler(guild):
        await bot.update_presence()

    async def on_guild_remove_handler(guild):
        await bot.update_presence()

    bot.add_listener(on_ready_handler, "on_ready")
    bot.add_listener(on_guild_join_handler, "on_guild_join")
    bot.add_listener(on_guild_remove_handler, "on_guild_remove")

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
