class Ability:
    def __init__(self, name, description, max_charges):
        self.name = name
        self.description = description
        self.max_charges = max_charges
        self.current_charges = self.max_charges

    def info(self):
        return f"{self.name}:\n{self.description}\nUses: {self.current_charges}/{self.max_charges}"

    def reset(self):
        self.current_charges = self.max_charges

    def use(self):
        if self.current_charges > 0:
            self.current_charges -= 1
            return True
        return False

    def set_max_charges(self, max_charges):
        self.max_charges = max_charges
        return "You can now use {self.name} a total of {max_charges} times!"

    def rename(self, new_name):
        self.name = new_name
