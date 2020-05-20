class Item:
    def __init__(self, name, description, quantity):
        self.name = name
        self.description = description
        self.quantity = quantity

    def info(self):
        return f"{self.name}:\n{self.description}\Quantity: {self.quantity}"

    def add(self, amount):
        self.quantity += amount

    def use(self):
        if self.quantity > 0:
            self.quantity -= 1
            return True
        return False