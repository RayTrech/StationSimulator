import random

class StationEvent:
    def __init__(self, name):
        self.name = name

    def apply(self, station):
        raise NotImplementedError


class MeteorEvent(StationEvent):
    def __init__(self):
        super().__init__("Meteor Impact")

    def apply(self, station):
        station.hull = max(0, station.hull - 20)
        return 'Meteor impact! Hull damaged by 20.'


class OxygenLeakEvent(StationEvent):
    def __init__(self):
        super().__init__('Oxygen Leak')

    def apply(self, station):
        station.oxygen = max(0, station.oxygen - 25)
        return 'Oxygen leak! Oxygen lost by 25.'


class ModuleFailureEvent(StationEvent):
    def __init__(self):
        super().__init__('Module Failure')

    def apply(self, station):
        if not station.modules:
            return f'Module failure occurred, but there are no modules.'
        module = random.choice(station.modules)
        module.damage(30)

        return f'Module failure! {module.name} damaged by 30.'


        

