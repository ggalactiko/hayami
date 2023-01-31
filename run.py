from colorama import Fore
from discord.ext import tasks
import discord
import asyncio
import os
from dotenv import load_dotenv
from main import MyBot

load_dotenv()

bot = MyBot("!")


async def load_cogs():
    for filename in os.listdir("./custom"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"custom.{filename[:-3]}")
                print(f"{Fore.LIGHTBLUE_EX}Loaded {filename}")
            except Exception as e:
                print(f"{Fore.LIGHTRED_EX}Failed to load {filename}")
                print(f"{Fore.LIGHTRED_EX}{e}")


@bot.tree.error
async def error_handler(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(str(error), ephemeral=True)
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message(str(error), ephemeral=True)
    if isinstance(error, discord.app_commands.BotMissingPermissions):
        await interaction.response.send_message(str(error), ephemeral=True)
    raise error


@tasks.loop(minutes=1)
async def run_every_minute():
    await bot.wait_until_ready()
    await bot.change_presence(activity=discord.Game(name="galactiko.net"))
    await asyncio.sleep(30)
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} Servers"))
    await asyncio.sleep(30)

@bot.event
async def on_ready():
    await load_cogs()
    await bot.tree.sync()
    print(f"{Fore.LIGHTBLUE_EX}{bot.user.name} is ready to go!, watching {len(bot.guilds)} servers, tree synced \n")
    run_every_minute.start()


async def start():
    await bot.login(os.getenv("TOKEN"))
    await bot.connect()


asyncio.run(start())
