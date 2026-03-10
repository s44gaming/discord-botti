"""
Hauskat minipelit – jokainen kytkettävissä web-dashboardista.
"""
import random
import discord
from discord import app_commands
from discord.ext import commands


class MinipelitCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kolikko", description="Heitä kolikkoa – kruuna vai klaava?")
    async def kolikko(self, interaction: discord.Interaction):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "kolikko"):
            await interaction.response.send_message(
                "⚠️ Tämä minipeli on poistettu käytöstä. Ota se käyttöön web-dashboardista.", ephemeral=True
            )
            return
        tulos = random.choice(("🪙 **Kruuna!**", "🪙 **Klaava!**"))
        await interaction.response.send_message(tulos)

    @app_commands.command(name="noppa", description="Heitä noppaa (esim. 1d6, 2d20)")
    @app_commands.describe(heitto="Esim. 1d6, 2d6, 1d20 (oletus 1d6)")
    async def noppa(self, interaction: discord.Interaction, heitto: str = "1d6"):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "noppa"):
            await interaction.response.send_message(
                "⚠️ Tämä minipeli on poistettu käytöstä. Ota se käyttöön web-dashboardista.", ephemeral=True
            )
            return
        try:
            parts = heitto.lower().replace("d", " ").split()
            if len(parts) != 2:
                raise ValueError("Käytä muotoa 1d6 tai 2d20")
            n, sivu = int(parts[0]), int(parts[1])
            if n < 1 or n > 10 or sivu < 2 or sivu > 100:
                raise ValueError("Määrä 1–10, silmäluku 2–100")
            tulokset = [random.randint(1, sivu) for _ in range(n)]
            total = sum(tulokset)
            if n == 1:
                msg = f"🎲 Noppa: **{tulokset[0]}** (d{sivu})"
            else:
                msg = f"🎲 Nopat: {tulokset} → yhteensä **{total}** ({n}d{sivu})"
            await interaction.response.send_message(msg)
        except (ValueError, IndexError):
            await interaction.response.send_message(
                "Käytä muotoa esim. `1d6` tai `2d20`. Ensimmäinen luku = heittojen määrä, toinen = nopan sivu.",
                ephemeral=True
            )

    @app_commands.command(name="8ball", description="Maaginen 8-pallo vastaa kysymykseesi")
    @app_commands.describe(kysymys="Kysy mitä tahansa")
    async def ball8(self, interaction: discord.Interaction, kysymys: str):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "8ball"):
            await interaction.response.send_message(
                "⚠️ Tämä minipeli on poistettu käytöstä. Ota se käyttöön web-dashboardista.", ephemeral=True
            )
            return
        vastaukset = [
            "Joo, ehdottomasti!", "Kyllä!", "Näyttää siltä.", "Todennäköisesti.",
            "En osaa sanoa.", "Kokeile myöhemmin.", "En nyt sano.",
            "Ei näytä hyvältä.", "Ei.", "Ehdottomasti ei.", "Älä luota siihen."
        ]
        vastaus = random.choice(vastaukset)
        await interaction.response.send_message(f"🔮 **{kysymys}**\n{vastaus}")

    @app_commands.command(name="kps", description="Kivi, paperi, sakset – vastaan botti")
    @app_commands.describe(valinta="Valintasi")
    @app_commands.choices(valinta=[
        app_commands.Choice(name="Kivi 🪨", value="kivi"),
        app_commands.Choice(name="Paperi 📄", value="paperi"),
        app_commands.Choice(name="Sakset ✂️", value="sakset"),
    ])
    async def kps(self, interaction: discord.Interaction, valinta: app_commands.Choice[str]):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "kps"):
            await interaction.response.send_message(
                "⚠️ Tämä minipeli on poistettu käytöstä. Ota se käyttöön web-dashboardista.", ephemeral=True
            )
            return
        bot_valinta = random.choice(("kivi", "paperi", "sakset"))
        emoji = {"kivi": "🪨", "paperi": "📄", "sakset": "✂️"}
        sinun, botti = valinta.value, bot_valinta
        if sinun == botti:
            tulos = "🤝 Tasapeli!"
        elif (sinun == "kivi" and botti == "sakset") or (sinun == "paperi" and botti == "kivi") or (sinun == "sakset" and botti == "paperi"):
            tulos = "🎉 Voitit!"
        else:
            tulos = "😅 Botti voitti!"
        await interaction.response.send_message(
            f"{emoji[sinun]} vs {emoji[botti]}\n{tulos}"
        )

    @app_commands.command(name="arvaa_luku", description="Arvaa luku 1–10 – botti arpoo oikean vastauksen")
    @app_commands.describe(luku="Arvauksesi (1–10)")
    async def arvaa_luku(self, interaction: discord.Interaction, luku: int):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "arvaa"):
            await interaction.response.send_message(
                "⚠️ Tämä minipeli on poistettu käytöstä.", ephemeral=True
            )
            return
        if luku < 1 or luku > 10:
            await interaction.response.send_message("Luvun pitää olla 1–10.", ephemeral=True)
            return
        oikea = random.randint(1, 10)
        if luku == oikea:
            await interaction.response.send_message(f"🎉 Oikein! Ajattelin lukua **{oikea}**.")
        else:
            await interaction.response.send_message(f"😅 Ei osunut. Ajattelin **{oikea}**, arvasit {luku}.")

    @app_commands.command(name="arpa", description="Arpa valitsee yhden annetuista vaihtoehdoista")
    @app_commands.describe(vaihtoehdot="Pilkulla erotetut vaihtoehdot, esim. pizza,kebab,salaatti")
    async def arpa(self, interaction: discord.Interaction, vaihtoehdot: str):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "arpa"):
            await interaction.response.send_message(
                "⚠️ Tämä minipeli on poistettu käytöstä. Ota se käyttöön web-dashboardista.", ephemeral=True
            )
            return
        opts = [x.strip() for x in vaihtoehdot.split(",") if x.strip()]
        if len(opts) < 2:
            await interaction.response.send_message(
                "Anna vähintään kaksi vaihtoehtoa pilkulla erotettuna, esim. `pizza, kebab, salaatti`.",
                ephemeral=True
            )
            return
        if len(opts) > 20:
            await interaction.response.send_message("Enintään 20 vaihtoehtoa.", ephemeral=True)
            return
        valittu = random.choice(opts)
        await interaction.response.send_message(f"🎱 **Arpa:** {valittu}")

    @app_commands.command(name="ruletti", description="Venäläinen ruletti – 1/6 mahdollisuus 'pum'")
    async def ruletti(self, interaction: discord.Interaction):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "ruletti"):
            await interaction.response.send_message(
                "⚠️ Tämä minipeli on poistettu käytöstä. Ota se käyttöön web-dashboardista.", ephemeral=True
            )
            return
        if random.randint(1, 6) == 1:
            await interaction.response.send_message("💥 **PUM!** 😵")
        else:
            await interaction.response.send_message("🔫 *klik* ... turvallinen kierros! 😮‍💨")


async def setup(bot):
    await bot.add_cog(MinipelitCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
