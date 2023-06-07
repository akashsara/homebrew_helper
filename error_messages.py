# This file contains all error messages in a single place for easy management.

DICE_TOO_HIGH = (
    "One or more of your rolls are absurdly high. I'm not rolling that <@{author_id}>. Max is {max_dice}d{largest_die}."
)

TOO_MANY_DICE = (
    "I'm not gonna roll that many dice <@{author_id}>. Max is {max_dice}."
)

WRONG_DICE_COMMAND = "That's not how you do it <@{author_id}>. Your roll should be of the format (roll)(operation)(modifier)(special), where rolls should be of the format XdN (X = Number of Dice; N = Number of Die Faces). Operation is either + or - and modifier is your modifier. Special indicates advantage or disadvantage. Just append your roll with an a or d. Examples: `?r 1d20+2` or `?r 1d20+1d4-2` or `?r 1d20a`."

UNKNOWN_ERROR = "An unforeseen error has occured. Please contact an administrator."

ROLL_WITH_REPEAT_INVALID_DIGIT = "<@{author_id}>, if you want to roll multiple times, do`?r <roll>r<num_times>` Note that <num_times> is an integer greater than 1."

INVALID_ROLL_TYPE = "Uh..<@{author_id}>, I have no idea what kind of roll that's supposed to be so I can't help you."