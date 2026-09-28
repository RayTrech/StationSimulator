import random

from crew import CrewMember, Engineer, Medic
from events import EVENT_TYPES
from modules import Laboratory, LifeSupport, Reactor, UpgradeError


def _read_integer(data, key, minimum=0, maximum=None):
    value = data.get(key)
    if (
        type(value) is not int
        or value < minimum
        or (maximum is not None and value > maximum)
    ):
        raise ValueError("Некорректное числовое значение в сохранении.")
    return value


def _read_name(data):
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Название или имя должно быть непустой строкой.")
    return name


class Station:
    daily_oxygen_cost = 15
    daily_energy_cost = 20
    event_probability = 0.4

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
        return self.hull <= 0 or not any(member.is_alive for member in self.crew)

    @property
    def mission_completed(self):
        return not self.is_destroyed and self.research >= self.research_goal

    def show_status(self):
        print(f"\n=== СОСТОЯНИЕ СТАНЦИИ «{self.name.upper()}» ===")
        print(f"День: {self.day}")
        print(f"Корпус: {self.hull}%")
        print(f"Энергия: {self.energy}%")
        print(f"Кислород: {self.oxygen}%")
        print(f"Исследования: {self.research}/{self.research_goal}")

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

    def upgrade_module(self, module):
        if module not in self.modules:
            raise UpgradeError("Выбранный модуль не принадлежит этой станции.")
        if self.is_destroyed or self.mission_completed:
            raise UpgradeError("Завершённую партию нельзя продолжать улучшениями.")
        cost = module.check_upgrade()
        engineer = next(
            (member for member in self.crew if isinstance(member, Engineer) and member.is_alive),
            None,
        )
        if engineer is None:
            raise UpgradeError("Для улучшения нужен живой инженер.")
        if engineer.energy < module.upgrade_energy_cost:
            raise UpgradeError("Инженеру нужно отдохнуть: требуется 20 энергии.")
        if self.research < cost:
            raise UpgradeError(f"Недостаточно исследований: требуется {cost}.")

        # Все проверки выполняются до списания ресурсов и изменения уровня.
        module.upgrade()
        self.research -= cost
        engineer.energy -= module.upgrade_energy_cost
        self.event_log.append(
            f"День {self.day}: модуль «{module.name}» улучшен до уровня {module.level}. "
            f"Потрачено {cost} исследований."
        )
        return cost

    def operate_modules(self):
        # Реактор работает первым, жизнеобеспечение получает приоритет над наукой.
        modules = sorted(
            self.modules,
            key=lambda module: (module.requires_energy, not isinstance(module, LifeSupport)),
        )
        for module in modules:
            if not module.is_operational:
                continue
            if module.requires_energy:
                if self.energy < module.energy_cost:
                    continue
                self.energy -= module.energy_cost
            resource, amount = module.operate()
            self.apply_module_output(resource, amount)

    def trigger_random_event(self):
        event = random.choice(EVENT_TYPES)()
        message = event.apply(self)
        self.event_log.append(f"День {self.day}: {message}")
        return message

    def apply_module_output(self, resource, amount):
        if resource == "energy":
            self.energy = min(100, self.energy + amount)
        elif resource == "oxygen":
            self.oxygen = min(100, self.oxygen + amount)
        elif resource == "research":
            self.research += amount
        else:
            raise ValueError("Неизвестный ресурс модуля.")

    def next_day(self):
        if self.is_destroyed or self.mission_completed:
            return False
        self.day += 1
        self.oxygen = max(0, self.oxygen - self.daily_oxygen_cost)
        self.energy = max(0, self.energy - self.daily_energy_cost)
        self.operate_modules()
        if random.random() < self.event_probability:
            self.trigger_random_event()
        if self.oxygen == 0:
            for member in self.crew:
                member.take_damage(10)
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
            "event_log": list(self.event_log),
            "crew": [member.to_dict() for member in self.crew],
            "modules": [module.to_dict() for module in self.modules],
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Сохранение должно содержать объект станции.")
        station = cls(_read_name(data))
        station.day = _read_integer(data, "day", minimum=1)
        for resource in ("oxygen", "energy", "hull"):
            setattr(station, resource, _read_integer(data, resource, maximum=100))
        station.research = _read_integer(data, "research")
        station.research_goal = _read_integer(data, "research_goal", minimum=1)

        # Старые сохранения не содержат журнала событий.
        event_log = data.get("event_log", [])
        if not isinstance(event_log, list) or not all(
            isinstance(entry, str) for entry in event_log
        ):
            raise ValueError("Журнал событий должен быть списком строк.")
        station.event_log = list(event_log)

        crew_types = {"CrewMember": CrewMember, "Engineer": Engineer, "Medic": Medic}
        module_types = {
            "Reactor": Reactor,
            "LifeSupport": LifeSupport,
            "Laboratory": Laboratory,
        }
        for key, types in (("crew", crew_types), ("modules", module_types)):
            items = data.get(key)
            if not isinstance(items, list):
                raise ValueError("Экипаж и модули должны быть списками.")
            for item in items:
                if not isinstance(item, dict) or not isinstance(item.get("type"), str):
                    raise ValueError("Некорректное описание члена экипажа или модуля.")
                item_type = types.get(item["type"])
                if item_type is None:
                    raise ValueError("Неизвестный тип члена экипажа или модуля.")
                name = _read_name(item)
                if key == "crew":
                    station.add_crew(
                        item_type(
                            name,
                            _read_integer(item, "health", maximum=100),
                            _read_integer(item, "energy", maximum=100),
                        )
                    )
                else:
                    module = item_type(name)
                    module.condition = _read_integer(item, "condition", maximum=100)
                    module.level = item.get("level", 1)
                    station.add_module(module)
        return station
