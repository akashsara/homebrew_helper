import os
import pickle
import defaultdict


def save_file(data, file_path):
    if data:
        with open(file_path, "wb") as fp:
            pickle.dump(data, fp)


def load_files(file_root_dir, file_dict):
    dicts = {
        "users": defaultdict(lambda: defaultdict(list)),
        "abilities": defaultdict(lambda: defaultdict(dict)),
        "items": defaultdict(lambda: defaultdict(dict)),
    }
    for key, value in file_dict.items():
        file_path = os.path.join(f"{file_root_dir}/{value}")
        if os.path.exists(file_path):
            with open(file_path, "rb") as fp:
                dicts[key] = pickle.load(fp)
    return dicts["users"], dicts["abilities"], dicts["items"]


def pad(text_to_pad, length_to_pad_to, direction):
    if direction == "left":
        return (" " * (length_to_pad_to - len(text_to_pad))) + text_to_pad
    return text_to_pad + (" " * (length_to_pad_to - len(text_to_pad)))


def format_rolls(rolls):
    new_roll = []
    for item in rolls:
        key, value = item
        num_dice, die_size = key.split("d")
        num_dice = pad(num_dice, 2, "left")
        die_size = pad(die_size, 3, "right")
        total = pad(str(sum(value)), 5, "left")
        new_roll.append(f"{num_dice}d{die_size}: {total} :: {value}")
    return "\n".join(new_roll)


def format_repeated_rolls(rolls):
    full_text = []
    ending = []
    for item in rolls:
        roll = item["user_roll"]
        all_in_one = []
        for _, y in item["rolls"]:
            all_in_one.extend(y)
        modifier = pad(str(item["modifier"]), 2, "left")
        total = pad(str(item["total"]), 5, "left")
        ending.append(item["total"])
        full_text.append(f"{roll} : {total} :: {modifier} + {all_in_one}")
    ending = f"Final Rolls: **{ending}**"
    return full_text, ending
