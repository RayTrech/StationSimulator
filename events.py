import random

from modules import Laboratory, Reactor


class StationEvent:
    def __init__(self, name):
        self.name = name

    def apply(self, station):
        raise NotImplementedError("Событие должно определять своё действие.")


class MeteorEvent(StationEvent):
    def __init__(self):
        super().__init__("Удар метеорита")

    def apply(self, station):
        station.hull = max(0, station.hull - 20)
        return "Удар метеорита! Корпус повреждён на 20 единиц."


class OxygenLeakEvent(StationEvent):
    def __init__(self):
        super().__init__("Утечка кислорода")

    def apply(self, station):
        station.oxygen = max(0, station.oxygen - 25)
        return "Утечка кислорода! Потеряно 25 единиц кислорода."


class ModuleFailureEvent(StationEvent):
    def __init__(self):
        super().__init__("Поломка модуля")

    def apply(self, station):
        if not station.modules:
            return "Произошла поломка, но на станции нет модулей."
        module = random.choice(station.modules)
        module.damage(40)
        return f"Поломка модуля! «{module.name}» повреждён на 40 единиц."


class SolarFlareEvent(StationEvent):
    def __init__(self):
        super().__init__("Солнечная вспышка")

    def apply(self, station):
        station.energy = max(0, station.energy - 30)
        reactor = next(
            (module for module in station.modules if isinstance(module, Reactor)),
            None,
        )
        message = "Солнечная вспышка! Потеряно 30 единиц энергии."
        if reactor is not None:
            reactor.damage(20)
            message += f" Реактор «{reactor.name}» повреждён на 20 единиц."
        return message


class MedicalEmergencyEvent(StationEvent):
    def __init__(self):
        super().__init__("Медицинская авария")

    def apply(self, station):
        survivors = [member for member in station.crew if member.is_alive]
        if not survivors:
            return "Медицинская авария: на станции нет живых членов экипажа."
        member = random.choice(survivors)
        member.take_damage(30)
        return f"Медицинская авария! {member.name}: потеряно 30 единиц здоровья."


class ScientificBreakthroughEvent(StationEvent):
    def __init__(self):
        super().__init__("Удачный научный эксперимент")

    def apply(self, station):
        if not any(
            isinstance(module, Laboratory) and module.is_operational
            for module in station.modules
        ):
            return "Научный эксперимент отложен: нет работающей лаборатории."
        station.research += 15
        return "Удачный научный эксперимент! Получено 15 единиц исследований."


EVENT_TYPES = (
    MeteorEvent,
    OxygenLeakEvent,
    ModuleFailureEvent,
    SolarFlareEvent,
    MedicalEmergencyEvent,
    ScientificBreakthroughEvent,
)
