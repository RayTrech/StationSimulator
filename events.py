import random

class StationEvent:
    def __init__(self, name):
        self.name = name

    def apply(self, station):
        raise NotImplementedError


class MeteorEvent(StationEvent):
    def __init__(self):
        super().__init__("Удар метеорита")

    def apply(self, station):
        station.hull = max(0, station.hull - 20)
        return 'Удар метеорита! Корпус повреждён на 20 единиц.'


class OxygenLeakEvent(StationEvent):
    def __init__(self):
        super().__init__('Утечка кислорода')

    def apply(self, station):
        station.oxygen = max(0, station.oxygen - 25)
        return 'Утечка кислорода! Потеряно 25 единиц кислорода.'


class ModuleFailureEvent(StationEvent):
    def __init__(self):
        super().__init__('Поломка модуля')

    def apply(self, station):
        if not station.modules:
            return f'Произошла поломка, но на станции нет модулей.'
        module = random.choice(station.modules)
        module.damage(40)

        return f'Поломка модуля! «{module.name}» повреждён на 40 единиц.'


        

