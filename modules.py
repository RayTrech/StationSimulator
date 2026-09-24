class StationModule:
    def __init__(self, name):
        self.name = name
        self.condition = 100

    @property
    def condition(self):
        return self._condition

    @condition.setter
    def condition(self, value):
        if 0 <= value <= 100:
            self._condition = value
        else:
            raise ValueError('Ошибка значения')

    def damage(self, amount):
        self.condition = max(0, self.condition - amount)

    def repair(self, amount):
        self.condition = min(100, self.condition + amount)

    def __str__(self):
        return f'{self.__class__.__name__} {self.name} | Condition: {self.condition}%'


class Reactor(StationModule):
    def __init__(self, name):
        super().__init__(name)
        self.power_output = 50

    def operate(self):
        if self.condition >= 70:
            return "energy", 50
        elif self.condition >= 30:
            return "energy", 25
        return "energy", 0
    

class LifeSupport(StationModule):
    def __init__(self, name):
        super().__init__(name)
        self.oxygen_output = 20

    def operate(self):
        if self.condition >= 70:
            return "oxygen", 20
        elif self.condition >= 30:
            return "oxygen", 10
        return "oxygen", 0


class Laboratory(StationModule):
    def __init__(self, name):
        super().__init__(name)
        self.research_output = 10

    def operate(self):
        if self.condition >= 70:
            return "research", 10
        elif self.condition >= 30:
            return "research", 5
        return "research", 0