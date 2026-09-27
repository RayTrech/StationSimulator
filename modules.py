class StationModule:
    module_type = "Модуль"

    def __init__(self, name):
        self.name = name
        self.condition = 100
        self.energy_cost = 0
        self.requires_energy = True

    @property
    def condition(self):
        return self._condition

    @condition.setter
    def condition(self, value):
        if type(value) is not int or not 0 <= value <= 100:
            raise ValueError("Состояние модуля должно быть целым числом от 0 до 100.")
        self._condition = value

    @property
    def is_operational(self):
        return self.condition >= 30

    def damage(self, amount):
        if type(amount) is not int or amount < 0:
            raise ValueError("Урон должен быть неотрицательным целым числом.")
        self.condition = max(0, self.condition - amount)

    def repair(self, amount):
        if type(amount) is not int or amount < 0:
            raise ValueError("Ремонт должен быть неотрицательным целым числом.")
        self.condition = min(100, self.condition + amount)

    def operate(self):
        raise NotImplementedError("Модуль должен определять свою выработку.")

    def output_for_condition(self, maximum):
        if self.condition >= 70:
            return maximum
        if self.is_operational:
            return maximum // 2
        return 0

    def __str__(self):
        return f"{self.module_type} «{self.name}» | Состояние: {self.condition}%"

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "condition": self.condition,
        }


class Reactor(StationModule):
    module_type = "Реактор"

    def __init__(self, name):
        super().__init__(name)
        self.power_output = 55
        self.requires_energy = False

    def operate(self):
        return "energy", self.output_for_condition(self.power_output)


class LifeSupport(StationModule):
    module_type = "Жизнеобеспечение"

    def __init__(self, name):
        super().__init__(name)
        self.oxygen_output = 20
        self.energy_cost = 20

    def operate(self):
        return "oxygen", self.output_for_condition(self.oxygen_output)


class Laboratory(StationModule):
    module_type = "Лаборатория"

    def __init__(self, name):
        super().__init__(name)
        self.research_output = 8
        self.energy_cost = 15

    def operate(self):
        return "research", self.output_for_condition(self.research_output)
