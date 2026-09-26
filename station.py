import random

from events import MeteorEvent, OxygenLeakEvent, ModuleFailureEvent
from crew import Engineer, Medic
from modules import Reactor, LifeSupport, Laboratory


class Station:
    def __init__(self, name):
        self.name = name
        self.oxygen = 100
        self.energy = 100
        self.hull = 100
        self.research_goal = 200

        self.crew = []
        self.modules = []
        self.event_log = []

        self.day = 1
        self.research = 0

    @property
    def is_destroyed(self):
        if self.hull == 0:
            return True

        if self.crew and all(
            not member.is_alive for member in self.crew
        ):
            return True

        return False

    @property
    def mission_completed(self):
        return self.research >= self.research_goal

    def show_status(self):
        print(
            f"\n=== СОСТОЯНИЕ СТАНЦИИ "
            f"«{self.name.upper()}» ==="
        )
        print(f"День: {self.day}")
        print(f"Корпус: {self.hull}%")
        print(f"Энергия: {self.energy}%")
        print(f"Кислород: {self.oxygen}%")
        print(
            f"Исследования: "
            f"{self.research}/{self.research_goal}"
        )

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
        resource_names = {
            "energy": "энергия",
            "oxygen": "кислород",
            "research": "исследования",
        }

        for module in self.modules:
            resource, amount = module.operate()

            resource_name = resource_names.get(
                resource,
                resource
            )

            print(
                f"{module.name}: "
                f"{resource_name} +{amount}"
            )

    def trigger_random_event(self):
        events = [
            MeteorEvent(),
            OxygenLeakEvent(),
            ModuleFailureEvent(),
        ]

        event = random.choice(events)
        message = event.apply(self)

        self.event_log.append(
            f"День {self.day}: {message}"
        )

        return message

    def apply_module_output(self, resource, amount):
        if resource == "energy":
            self.energy = min(
                100,
                self.energy + amount
            )

        elif resource == "oxygen":
            self.oxygen = min(
                100,
                self.oxygen + amount
            )

        elif resource == "research":
            self.research += amount

    def next_day(self):
        if self.is_destroyed:
            return False

        # 1. Станция расходует ресурсы
        self.oxygen = max(
            0,
            self.oxygen - 15
        )

        self.energy = max(
            0,
            self.energy - 20
        )

        # 2. Сначала работают автономные модули
        # Например Reactor
        for module in self.modules:
            if not module.requires_energy:
                resource, amount = module.operate()

                self.apply_module_output(
                    resource,
                    amount
                )

        # 3. Затем работают модули,
        # которым требуется энергия
        for module in self.modules:
            if (
                module.requires_energy
                and self.energy >= module.energy_cost
            ):
                self.energy -= module.energy_cost

                resource, amount = module.operate()

                self.apply_module_output(
                    resource,
                    amount
                )

        if random.random() < 0.3:
            self.trigger_random_event()


        if self.oxygen == 0:
            for member in self.crew:
                member.take_damage(10)

        self.day += 1

        return True

    def to_dict(self):
        return {
            "name": self.name,
            "day": self.day,
            "oxygen": self.oxygen,
            "energy": self.energy,
            "hull": self.hull,
            "research": self.research,
            "research_goal": self.research_goal,

            "crew": [
                member.to_dict()
                for member in self.crew
            ],

            "modules": [
                module.to_dict()
                for module in self.modules
            ],
        }

    @classmethod
    def from_dict(cls, data):
        station = cls(data["name"])

        station.day = data["day"]
        station.oxygen = data["oxygen"]
        station.energy = data["energy"]
        station.hull = data["hull"]
        station.research = data["research"]
        station.research_goal = data["research_goal"]

        for member_data in data["crew"]:
            if member_data["type"] == "Engineer":
                member = Engineer(
                    member_data["name"],
                    member_data["health"],
                    member_data["energy"],
                )

            elif member_data["type"] == "Medic":
                member = Medic(
                    member_data["name"],
                    member_data["health"],
                    member_data["energy"],
                )

            else:
                continue

            station.add_crew(member)

    
        for module_data in data["modules"]:
            if module_data["type"] == "Reactor":
                module = Reactor(
                    module_data["name"]
                )

            elif module_data["type"] == "LifeSupport":
                module = LifeSupport(
                    module_data["name"]
                )

            elif module_data["type"] == "Laboratory":
                module = Laboratory(
                    module_data["name"]
                )

            else:
                continue

           
            module.condition = module_data["condition"]

            station.add_module(module)

        return station