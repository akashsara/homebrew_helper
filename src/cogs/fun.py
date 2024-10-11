from discord.ext import commands
import src.templates as templates
import asyncio
import random


# Ref: https://stackoverflow.com/questions/65595213/how-to-add-shared-cooldown-to-multiple-discord-py-commands
class FunStuff(commands.Cog):
    def __init__(self, bot, n_messages=3, cooldown=10):
        self.bot = bot
        self.cooldown = commands.CooldownMapping.from_cooldown(
            n_messages, cooldown, commands.BucketType.user
        )

    async def cog_check(self, context):
        # Don't use a cooldown with the help command.
        if context.invoked_with == "help":
            return True
        bucket = self.cooldown.get_bucket(context.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            # You're rate limited, send message here
            await context.send(
                f"<@{context.author.id}>: Stop spamming! Please wait {round(retry_after, 2)} seconds to use the command."
            )
            return False
        return True

    @commands.Cog.listener()
    async def on_command_error(self, context, error):
        # Empty error handler so we don't get the error from the `cog_check` func in the terminal
        if isinstance(error, commands.CheckFailure):
            pass
        else:
            print(error)

    @commands.command(
        name="git",
        help="Check out my Github repository! Feel free to contribute!",
        brief="Github repository link.",
    )
    async def git(self, context):
        await context.send("Hello! Check out my source code here: https://github.com/akashsara/homebrew_helper")

    @commands.command(
        name="bungee_gum",
        aliases=["bg", "bungee", "gum", "bungeegum"],
        help="When you really want to know about Bungee Gum.",
        brief="Hisoka's favorite food.",
    )
    async def bungee_gum(self, context):
        await context.send(
            f"<@{context.author.id}>, bungee gum possesses the properties of both rubber and gum."
        )

    @commands.command(
        name="cow",
        aliases=["moo"],
        help="What does the cow say?",
        brief="What does the cow say?",
    )
    async def cow(self, context):
        await context.send(f"MOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.")

    @commands.command(
        name="rick",
        aliases=["rickroll"],
        help="I wonder what this does?",
        brief="Try it out!",
    )
    async def rickroll(self, context):
        selection = random.choice(templates.RICK_ROLL_LYRICS)
        await context.send("```" + "\n".join(selection) + "```")

    @commands.command(
        name="fighting_words",
        aliases=["insult", "banter", "trash_talk"],
        help="For when you really want to banter but have nothing to say.",
        brief="Insulting, bantery or trash talk-y phrases.",
    )
    async def fighting_words(self, context):
        selection = random.choice(templates.FIGHTING_WORDS)
        await context.send(selection)

    @commands.command(
        name="wise_words",
        aliases=["wise", "wisdom"],
        help="When you need some inspirational or wise quotes.",
        brief="Wise or inspirational quotes.",
    )
    async def wise_words(self, context):
        quote = random.choice(templates.WISE_QUOTES)
        await context.send(quote)

    @commands.command(
        name="oracle",
        help="Need to make a decision? Ask the oracle!",
        brief="Ask me a question!",
    )
    async def oracle(self, context):
        author = f"<@{context.author.id}>"
        message = context.message.content[8:]
        await context.send(
            f"{author}: {message}\nAnswer: {random.choice(templates.ORACLE_ANSWERS)}"
        )

    @commands.command(
        name="report",
        aliases=["report_lan"],
        help="When you want to 'report' someone.",
        brief="Report people for reportable activities.",
    )
    async def report(self, context, target=None):
        author = f"<@{context.author.id}>"
        message = await context.send(f"{author}: Please wait...preparing report.")
        await asyncio.sleep(2)
        await message.edit(content="Report Prepared.")
        await asyncio.sleep(2)
        if random.randint(0, 100) == 69:
            await message.edit(
                content=f"Thank you for reporting {random.choice(templates.REPORTABLE_PEOPLE)}, {author}!"
            )
        elif target:
            await message.edit(content=f"Thank you for reporting {target}, {author}!")
        else:
            await message.edit(
                content=f"Thank you for reporting {templates.ALWAYS_REPORT}, {author}!"
            )

    @commands.command(
        name="slap",
        help="Slap someone.",
        brief="Slap someone .-.",
    )
    async def slap(self, context, target):
        author = f"<@{context.author.id}>"
        await context.send(f"{author} _slaps_ {target}")

    @commands.command(
        name="bonk",
        help="Bonk someone.",
        brief="Bonk someone for...reasons",
    )
    async def bonk(self, context, target):
        author = f"<@{context.author.id}>"
        await context.send(f"Doge: _bonks_ {target}. Off to jail.")

    @commands.command(
        name="niceone",
        aliases=["nice", "n1", "nice_one"],
        help="When you want to praise someone.",
        brief="Praise someone!",
    )
    async def niceone(self, context, target):
        quote = random.choice(templates.NICE_ONE_OPTIONS)
        await context.send(f"{quote} {target}!")

    @commands.command(
        name="wow",
        help="When you're amazed by someone.",
        brief="Express your amazement!",
    )
    async def wow(self, context, target):
        await context.send(f"W{'O' * random.randint(1, 20)}W {target}!")

    @commands.command(
        name="getrekt",
        aliases=["rekt", "get_rekt", "wrecked"],
        help="When someone has gotten 'rekt'.",
        brief="A good reaction to some banter.",
    )
    async def getrekt(self, context, target):
        await context.send(f"Get rekt {target}!")

    @commands.command(
        name="nikesh",
        help="Use this whenever someone tries to play the fool with you.",
        brief="If you know Nikesh.",
    )
    async def nikesh(self, context, target):
        await context.send(f"Don't try to play the fool with me Nikesh ({target})!")

    @commands.command(
        name="niceflame",
        aliases=["nice_flame"],
        help="When you want to mock or appreciate some trash talk.",
        brief="Appreciate some banter!",
    )
    async def niceflame(self, context, target):
        quote = random.choice(templates.NICE_FLAME_OPTIONS)
        await context.send(quote.format(target))

    @commands.command(
        name="dis",
        help="When you want to identify someone.",
        brief="Not a diss.",
    )
    async def dis(self, context, target):
        quote = random.choice(templates.DIS_OPTIONS)
        await context.send(quote.format(target))

    @commands.command(
        name="pdp",
        help="When you're unsure about things and want to leave it to the future.",
        brief="We'll see.",
    )
    async def pdp(self, context):
        await context.send("Paakalaam da paakalaam.")

    @commands.command(
        name="mmdmm",
        help="When you know someone is mocking you.",
        brief="Please stop mocking me.",
    )
    async def mmdmm(self, context):
        await context.send("Mock me da mock me.")


async def setup(bot):
    await bot.add_cog(FunStuff(bot))
