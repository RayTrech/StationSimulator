class CrewMember:
    def __init__(self, name, health, energy):
        self.name = name
        self.health = health
        self.energy = energy

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if 0 <= value <= 100:
            self._health = value
        else:
            raise ValueError('Ошибка значения')

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        if 0 <= value <= 100:
            self._energy = value
        else:
            raise ValueError('Ошибка значения')

    def rest(self):
        self.energy = min(100, self.energy + 20)

    def __str__(self):
        return f'{self.__class__.__name__} {self.name} | Health: {self.health} | Energy: {self.energy}'


class Engineer(CrewMember):
    def work(self):
        self.energy = max(0, self.energy - 15)

    def repair_module(self, module):
        if self.energy >= 15:
            module.repair(30)
            self.energy -= 15
            return True

        
        return False


class Medic(CrewMember):
    def work(self):
        self.energy = max(0, self.energy - 8) 