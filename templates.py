# This file contains all templates used by the bot in a single file.

# Dice Command
NORMAL_ROLL = "<@{author_id}>'s Roll:\n```fix\nYou rolled a {user_roll}.\nYou got: \n{result}\nYour modifier is: {modifier}```Your total roll is: **{total}**"

ROLL_WITH_ADV_DISADV = "<@{author_id}>:\n Attempt 1:\n```fix\nYou rolled a {user_first_roll}.\nYou got: \n{first_result}\nYour modifier is: {first_modifier}\nYour total roll is: {first_total}```Attempt 2:\n```fix\nYou rolled a {user_second_roll}.\nYou got: \n{second_result}\nYour modifier is: {second_modifier}\nYour total roll is: {second_total}```Your final roll is: **{final_result}**."

ROLL_WITH_REPEATS_STARTING_STRING = "<@{author_id}>'s Roll:\n```fix\nYou rolled {roll}."
ROLL_WITH_REPEATS_ENDING_STRING = "```Final Rolls: **{final_rolls}**"

# Roll initiative command
ROLL_INITIATIVE_START_STRING = "Roll Order:\n```\n+--------------+--------------------------------------+\n| Roll         | Player Name                          |\n+--------------+--------------------------------------+"
ROLL_INITIATIVE_END_STRING = "\n+--------------+--------------------------------------+```"
ROLL_INITIATIVE_INSTRUCTIONS = f"React with,\n⚔️ to add to the initiative order (or)\n👍 to add to the initiative order with advantage (or) 👎 to add to the initiative order with disadvantage\nand 🛑 to start rolling"
    

# Report Command
REPORTABLE_PEOPLE = ["Songs", "rtzGod"]
ALWAYS_REPORT = "Lan"

# Dis Command
DIS_OPTIONS = [
    "This {}...",
    "Dis {}",
    "This {}",
    "Dis {} no",
    "OMG dis {}",
    "omg this {}",
]

# Nice Flame Command
NICE_FLAME_OPTIONS = [
    "Nice flame {}!",
    "Woah! Calm down he has a family, {}!",
    "Someone call a firetruck for {}!",
    "Is it getting hot in here or what, {}?",
]

# Nice One Command
NICE_ONE_OPTIONS = [
    "Nice one",
    "NICE one",
    "nice ONE",
    "nIcE oNe",
    "NICE ONE",
    "That was really nice",
    "My humblest congratulations for a particularly pleasant action",
    "Woah, that was a nice one",
    "Niiiiiiiiiiiiiiiiiice one",
    "Niiiiiiiiiiiiice one",
]

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
    "It is never too late to be what you might have been. - George Eliot",
    "If you're not getting better you're getting worse - Joe Paterno",
    "Do or do not. There is no try -  Yoda",
    "Appear weak when you are strong, and strong when you are weak - Sun Tsu",
    "It's okay to lose to opponent. It's never okay to lose to fear - Mr. Miyagi",
    "Anything is possible when you have inner peace - Master Shifu",
    "All we have to decide is what to do with the time that is given to us - Gandalf the Grey",
    "Respect your efforts, respect yourself. Self-respect leads to self-discipline. When you have both firmly under your belt, that’s real power – Clint Eastwood",
    "You either die a hero, or live long enough to see yourself become the villain - Harvey Dent",
    "It takes a great deal of bravery to stand up to our enemies, but just as much to stand up to our friends. - Prof Albus Dumbledore",
    "It's the possibility of having a dream come true that makes life interesting. - Paulo Ceolho, The Alchemist",
    "The only way to learn is to live. - Matt Haig, The Midnight Library",
    "If you can't explain it to a six year old, you don't understand it yourself. - Albert Einstein",
    "Happiness can be found, even in the darkest of times, if one only remembers to turn on the light. - Prof Albus Dumbledore",
    "You must be the change you wish to see in the world. - Mahatma Gandhi",
    "Let us always meet each other with a smile, for the smile is the beginning of love. - Mother Teresa",
    "A dream is not that which you see while sleeping, it is something that does not let you sleep. - Dr APJ Abdul Kalam",
    "Never take your eyes off your opponent...  Even when you're bowing! - Bruce Lee",
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
    "You have miles to go before you reach mediocre.",
    "You're as useful as wet toilet paper.",
    "Zombies eat brains. You’re safe.",
    "Mirrors can’t talk, lucky for you they can’t laugh either.",
    "I don’t believe in plastic surgery, But in your case, Go ahead.",
    "You look like something I’d draw with my left hand.",
    "The best part about me, is I’m not you.",
    "I would like to confirm that I do not care.",
    "You are a sad strange little man, and you have my pity.",
    "Say hello to my little friend.",
    "Adios mothaf**ka!!",
    "I have a hand. You have a throat. Pray the two never have to meet.",
    "Rest in Peace.",
    "I have eaten better fighters than you.",
]
