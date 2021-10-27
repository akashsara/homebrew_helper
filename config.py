import os

TOKEN = os.environ.get("HOMEBREW_HELPER_TOKEN")
DB_TOKEN = os.environ.get("DATABASE_TOKEN")
BOT_PREFIX = ("?", "!")
ALLOWED_STATS = [
    "dex",
    "con",
    "cha",
    "kno",
    "wis",
    "str",
    "atk",
    "def",
    "speed",
    "max_hp",
    "current_hp",
]

VALID_ROLL_CHARACTERS = set(str(x) for x in range(0, 10)).union(
    {"+", "-", "d", " ", "(", ")"}
)

COIN_TOSS_MAX_TOSSES = 20
INITIATIVE_MAX_NPCS = 20
DICE_ROLL_MAX_DICE = 50
DICE_ROLL_LARGEST_DIE = 100
DISCORD_ID_REGEX = "(<@!\d+>)"

TOO_HIGH = (
    "One or more of your rolls are absurdly high. I'm not rolling that <@{author_id}>."
)

WRONG = "That's not how you do it <@{author_id}>. Your roll should be of the format (roll)(operation)(modifier)(special), where rolls should be of the format XdN (X = Number of Dice; N = Number of Die Faces). Operation is either + or - and modifier is your modifier. Special indicates advantage or disadvantage. Just append your roll with an a or d. Examples: `?r 1d20+2` or `?r 1d20+1d4-2` or `?r 1d20a`."

######################################################################
############# Used Specifically For Certain Bot Commands #############
######################################################################
# Report Command
REPORTABLE_PEOPLE = ["Songs", "rtzGod"]
ALWAYS_REPORT = "Lan"

# Rick Roll Command
RICK_ROLL_LYRICS = [
    [
        "♫♫♫ We're no strangers to love ♫♫♫",
        "♫♫♫ You know the rules and so do I ♫♫♫",
    ],
    [
        "♫♫♫ A full commitment's what I'm thinking of ♫♫♫",
        "♫♫♫ You wouldn't get this from any other guy ♫♫♫",
    ],
    [
        "♫♫♫ I just wanna tell you how I'm feeling ♫♫♫",
        "♫♫♫ Gotta make you understand ♫♫♫",
    ],
    [
        "♫♫♫ Never gonna give you up ♫♫♫",
        "♫♫♫ Never gonna let you down ♫♫♫",
        "♫♫♫ Never gonna run around and desert you ♫♫♫",
        "♫♫♫ Never gonna make you cry ♫♫♫",
        "♫♫♫ Never gonna say goodbye ♫♫♫",
        "♫♫♫ Never gonna tell a lie and hurt you ♫♫♫",
    ],
]

# Oracle Command
ORACLE_ANSWERS = [
    "HELL YEAH",
    "Yes.",
    "That is an excellent question.",
    "Wouldn't you like to know, weather boy?",
    "No.",
    "Nope.",
    "Nah man.",
    "Yup yup!",
    "Maybe",
    "idk lol",
    "Things will make sense when they make sense.",
    "It's all part of the plan",
    "It is known.",
    "No chance.",
    "Yes, 100%.",
    "Ask again later.",
    "The Oracle you're trying to reach is currently unavailable. Please hold the line or try again later.",
    "Don't count on it.",
    "My sources say no.",
    "Don't try to play the fool with me Nikesh.",
]

# Wise Words Command
WISE_QUOTES = [
    "You only live once, but if you do it right, once is enough. ― Mae West",
    "Between stimulus and response there is a space. In that space is our power to choose our response. In our response lies our growth and our freedom. - Viktor Frankl",
    "Courage doesn't always roar. Sometimes courage is the little voice at the end of the day that says I'll try again tomorrow. - Mary Anne Radmacher",
    "We are what we repeatedly do. Excellence, then, is not an act, but a habit. - Aristotle",
    "The journey of a thousand miles begins with one step. - Lao Tzu",
    "The only true wisdom is in knowing you know nothing. - Socrates",
    "It's not what happens to you, but how you react to it that matters. - Epictetus",
    "The woman who follows the crowd will usually go no further than the crowd. The woman who walks alone is likely to find herself in places no one has been before. - Albert Einstein",
    "The man who asks a question is a fool for a minute, the man who does not ask is a fool for life. - Confucius",
    "Happiness and freedom begin with one principle. Some things are within your control and some are not. - Epictetus",
    "Life isn’t about finding yourself; it’s about creating yourself. So live the life you imagined. - Henry David Thoreau",
    "Success is not final, failure is not fatal, it is the courage to continue that counts. - Winston Churchill",
    "Don't judge each day by the harvest you reap but by the seeds that you plant. - Robert Louis Stevenson",
    "You have brains in your head. You have feet in your shoes. You can steer yourself any direction you choose. - Dr. Seuss",
    "In three words I can sum up everything I've learned about life: it goes on. - Robert Frost",
    "The only person you are destined to become is the person you decide to be. - Ralph Waldo Emerson",
    "Whether you think you can or you think you can't, you're right. - Henry Ford",
    "It does not matter how slowly you go as long as you do not stop. - Confucius",
    "The best preparation for tomorrow is doing your best today. - H. Jackson Brown, Jr.",
    "It is never too late to be what you might have been. - George Eliot"
]
  
# Fighting Words Command
FIGHTING_WORDS = [
    "I'm surprised you manage to remember to brush your teeth in the morning.",
    "I came here to kick butt and chew bubblegum, and I'm all out of gum.",
    "You fight like a dairy farmer!",
    "I once owned a dog that was smarter than you.",
    "You bark like a dog. If I throw a stick, will you leave?",
    "Have you stopped wearing diapers yet?",
    "I've got a lesson for you to learn today.",
    "Would you like to be buried or cremated?",
    "There's one person too many in this room, and that's you.",
    "Your mother was a hamster and your father smelt of elderberries.",
    "To call you stupid would be an insult to stupid people!",
    "I've known sheep that could outwit you.",
    "You are one bit short of a byte.",
    "People clap when they see you. They clap their hands over their eyes.",
    "Your inferiority complex is fully justified.",
    "You have delusions of adequacy.",
    "It is impossible to underestimate you.",
    "I'm jealous of the people who haven't met you.",
    "You are more disappointing than an unsalted pretzel.",
    "You remind me to take out the trash.",
    "You have miles to go before you reach mediocre."
]
