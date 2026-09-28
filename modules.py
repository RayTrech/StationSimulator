class UpgradeError(ValueError):
    """Улучшение невозможно без изменения текущего состояния игры."""


class StationModule:
    module_type = "Модуль"
    max_level = 3
    upgrade_costs = (40, 60)
    upgrade_energy_cost = 20

    def __init__(self, name):
        self.name = name
        self.condition = 100
        self.level = 1
        self.enabled = True
        self.energy_cost = 0
        self.requires_energy = True

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if type(value) is not bool:
            raise ValueError("Питание модуля должно быть включено или выключено.")
        self._enabled = value

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        if type(value) is not int or not 1 <= value <= self.max_level:
            raise ValueError("Уровень модуля должен быть целым числом от 1 до 3.")
        self._level = value

    @property
    def upgrade_cost(self):
        if self.level == self.max_level:
            return 0
        return self.upgrade_costs[self.level - 1]

    def check_upgrade(self):
        if self.level == self.max_level:
            raise UpgradeError("Модуль уже достиг максимального уровня.")
        if self.condition < 70:
            raise UpgradeError("Сначала отремонтируйте модуль до состояния не ниже 70%.")
        return self.upgrade_cost

    def upgrade(self):
        self.check_upgrade()
        self.level += 1

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
        return self.enabled and self.condition >= 30

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
        if not self.is_operational:
            return 0
        if self.condition >= 70:
            return maximum
        return maximum // 2

    def __str__(self):
        power = "включено" if self.enabled else "выключено"
        return (f"{self.module_type} «{self.name}» | Состояние: {self.condition}% | "
                f"Уровень: {self.level}/{self.max_level} | Питание: {power}")

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "condition": self.condition,
            "level": self.level,
            "enabled": self.enabled,
        }


class Reactor(StationModule):
    module_type = "Реактор"

    def __init__(self, name):
        super().__init__(name)
        self.requires_energy = False

    @property
    def power_output(self):
        return 55 + 10 * (self.level - 1)

    def operate(self):
        return "energy", self.output_for_condition(self.power_output)


class LifeSupport(StationModule):
    module_type = "Жизнеобеспечение"

    def __init__(self, name):
        super().__init__(name)
        self.energy_cost = 20

    @property
    def oxygen_output(self):
        return 20 + 5 * (self.level - 1)

    def operate(self):
        return "oxygen", self.output_for_condition(self.oxygen_output)


class Laboratory(StationModule):
    module_type = "Лаборатория"

    def __init__(self, name):
        super().__init__(name)
        self.energy_cost = 15

    @property
    def research_output(self):
        return 8 + 4 * (self.level - 1)

    def operate(self):
        return "research", self.output_for_condition(self.research_output)
