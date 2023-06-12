# This file contains all error messages in a single place for easy management.

# Error messages for roll_wrapper (roll command)
ROLL_WRAPPER_DICE_TOO_HIGH = "One or more of your rolls are absurdly high. I'm not rolling that <@{author_id}>. Max is {max_dice}d{largest_die}."
ROLL_WRAPPER_TOO_MANY_DICE = (
    "I'm not gonna roll that many dice <@{author_id}>. Max is {max_dice}."
)
ROLL_WRAPPER_WRONG_DICE_COMMAND = "That's not how you do it <@{author_id}>. Your roll should be of the format (roll)(operation)(modifier)(special), where rolls should be of the format XdN (X = Number of Dice; N = Number of Die Faces). Operation is either + or - and modifier is your modifier. Special indicates advantage or disadvantage. Just append your roll with an a or d. Examples: `?r 1d20+2` or `?r 1d20+1d4-2` or `?r 1d20a`."
ROLL_WRAPPER_UNKNOWN_ERROR = (
    "An unforeseen error has occured. Please contact an administrator."
)
ROLL_WRAPPER_ROLL_WITH_REPEAT_INVALID_DIGIT = "<@{author_id}>, if you want to roll multiple times, do`?r <roll>r<num_times>` Note that <num_times> is an integer greater than 1."
ROLL_WRAPPER_INVALID_ROLL_TYPE = "Uh..<@{author_id}>, I have no idea what kind of roll that's supposed to be so I can't help you."

# Error messages for roll initiative command
ROLL_INITIATIVE_TOO_MANY_NPCS = "Um...if you have more than {max_npcs} NPCs in combat, please don't. I'm considering only {max_npcs}."
ROLL_INITIATIVE_INVALID_NPCS = "That isn't a valid number of NPCs!"
ROLL_INITIATIVE_TIMEOUT = "Look, a minute's gone by and I'm not waiting anymore."
ROLL_INITIATIVE_WRONG_USER = "Only <@{user}> can start the roll"
ROLL_INITIATIVE_NOT_ENOUGH_PLAYERS = "Thank you for wasting my time :)"
