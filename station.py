import random

from events import MeteorEvent, OxygenLeakEvent, ModuleFailureEvent

class Station:
    def __init__(self, name):
        self.name = name
        self.oxygen = 100
        self.energy = 100
        self.hull = 100
        self.crew = []
        self.modules = []
        self.event_log = []
        self.day = 1
        self.research = 0

    def add_crew(self, member):
        self.crew.append(member)

    def add_module(self, module):
        self.modules.append(module)

    def show_crew(self):
        for member in self.crew:
            print(member)

    def show_modules(self):
        for module in self.modules:
            print(module)

    def operate_modules(self):
        for module in self.modules:
            result = module.operate()
            print(f'{module.name} produced: {result}')

    def trigger_random_event(self):
        events = [
            MeteorEvent(),
            OxygenLeakEvent(),
            ModuleFailureEvent()
        ]

        event = random.choice(events)
        message = event.apply(self)
        
        self.event_log.append(f"Day {self.day}: {message}")
        return message

        
    def next_day(self):
        self.oxygen = max(0, self.oxygen - 15)
        self.energy = max(0, self.energy - 20)
        
        for module in self.modules:
            resource, amount = module.operate()

            if resource == 'energy':
                self.energy  = min(100, self.energy + amount)
            elif resource == 'oxygen':
                self.oxygen  = min(100, self.oxygen + amount)
            elif resource == 'research':
                self.research += amount

        if random.random() < 0.3:
            self.trigger_random_event()
        
        self.day += 1