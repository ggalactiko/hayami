import random
import typing as t
from discord.ext import commands
import discord
from utils import DataBase
import re
from io import BytesIO
import requests
from PIL import Image


class Phrase:
    def __init__(self, data: t.Tuple):
        self.data = data
        self.pattern = re.compile("\[(.*?)]")
        self.get_tags()

    @property
    def id(self) -> int:
        return self.data[0]

    def get_tags(self):
        self.tags = self.pattern.findall(self.data[1])
        self.parse_attachments()

    def parse_attachments(self):
        atcs = []
        for i in self.tags:
            if i.startswith("attachment"):
                result = i.split(";")[1]
                atcs.append(result)
        self.attachments = atcs

    @property
    def content(self):
        return re.sub(r"\[(.*?)]", "", self.data[1])


class Xd(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DataBase.create_connection("database/responses.sqlite")

    def get_from_db(self, temp: int):
        query = f"""
        SELECT 
        * 
        FROM 
        responses
        WHERE
        category = {temp}
        """
        results = self.db.read_query(query)
        return results

    def get_results(self, temperature):
        results = []
        if isinstance(temperature, list):
            for i in temperature:
                result = self.get_from_db(temp=i)
                results.append(result)
        elif isinstance(temperature, int):
            result = self.get_from_db(temp=temperature)
            results.append(result)
        return results

    async def get_item(self, category: list | int) -> Phrase:
        datas = []
        results = self.get_results(category)
        if len(results) < 1:
            for result in results[0]:
                datas.append(Phrase(result))
        else:
            for result in results:
                for owo in result:
                    datas.append(Phrase(owo))
        try:
            item = random.choice(datas)
            return item
        except:
            return Phrase(
                data=(0, "`Error 404` - Not Found", 0)
            )

    async def parse_temperature(self, m: discord.Message) -> list | int:
        message = m.content
        if "--any" in message:
            return [1, 2, 3]
        elif "--cat:1" in message:
            return 1
        elif "--cat:2" in message:
            return 2
        elif "--cat:3" in message:
            return 3
        elif "-racism" in message:
            return 2
        elif "-gay" in message:
            return 1
        else:
            return [1, 2]

    counter = {}

    def get_attchs(self, at: list):
        totals = []
        if len(at) > 0:
            for x in at:
                response = requests.get(x)
                img = Image.open(BytesIO(response.content))
                totals.append(img)
            result = self.create_files(totals)
            if len(result) > 0:
                return result
            return None

        return None

    def create_files(self, bt: list):
        files = []
        for o in bt:
            with BytesIO() as image_binary:
                o.save(image_binary, "PNG")
                image_binary.seek(0)
                files.append(discord.File(image_binary, filename='image.png'))
        return files

    async def temporized_msg(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild.id not in self.counter:
            self.counter[message.guild.id] = 0
            return
        self.counter[message.guild.id] += 1
        if self.counter[message.guild.id] >= 20:
            self.counter[message.guild.id] = 0
            response = await self.get_item(category=[1, 3])
            await message.channel.send(response.content, files=self.get_attchs(response.attachments))
        return 0

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        await self.temporized_msg(m)
        if (f"<@{self.bot.user.id}>" in m.content) and (not m.author.bot):
            cat = await self.parse_temperature(m)
            response = await self.get_item(category=cat)
            await m.reply(response.content, files=self.get_attchs(response.attachments))


async def setup(bot: commands.Bot):
    await bot.add_cog(Xd(bot))
