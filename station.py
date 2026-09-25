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

    @property
    def is_destroyed(self):
        if self.hull == 0:
            return True
        elif self.crew and all(not member.is_alive for member in self.crew):
            return True
        return False

    def show_status(self):
        print(f"\n=== {self.name.upper()} STATUS ===")
        print(f"Day: {self.day}")
        print(f"Hull: {self.hull}%")
        print(f"Energy: {self.energy}%")
        print(f"Oxygen: {self.oxygen}%")
        print(f"Research: {self.research}")

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

        self.event_log.append(f'Day {self.day}: {message}')
        return message

    def apply_module_output(self, resource, amount):
        if resource == 'energy':
            self.energy = min(100, self.energy + amount)

        elif resource == 'oxygen':
            self.oxygen = min(100, self.oxygen + amount)

        elif resource == 'research':
            self.research += amount

    def next_day(self):
        if self.is_destroyed:
            return False
        
        # 1. Станция расходует ресурсы
        self.oxygen = max(0, self.oxygen - 15)
        self.energy = max(0, self.energy - 20)

        # 2. Сначала работают автономные модули
        # Например Reactor
        for module in self.modules:
            if not module.requires_energy:
                resource, amount = module.operate()
                self.apply_module_output(resource, amount)

        # 3. Затем работают модули, которым нужна энергия
        # Например LifeSupport и Laboratory
        for module in self.modules:
            if module.requires_energy and self.energy > 0:
                resource, amount = module.operate()
                self.apply_module_output(resource, amount)

        if random.random() < 0.3:
            self.trigger_random_event()

        if self.oxygen == 0:
            for member in self.crew:
                member.take_damage(10)

        self.day += 1
        return True