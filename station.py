class Station:
    def __init__(self, name):
        self.name = name
        self.oxygen = 100
        self.energy = 100
        self.hull = 100
        self.crew = []

    def add_crew(self, member):
        self.crew.append(member)

    def show_crew(self):
        for member in self.crew:
            print(member)
