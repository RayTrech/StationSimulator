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

    @property
    def is_alive(self):
        return self.health > 0

    def rest(self):
        self.energy = min(100, self.energy + 20)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def __str__(self):
        return f'{self.__class__.__name__} {self.name} | Health: {self.health} | Energy: {self.energy}'


class Engineer(CrewMember):
    def work(self):
        self.energy = max(0, self.energy - 15)

    def repair_module(self, module):
        if self.is_alive and self.energy >= 15:
            module.repair(30)
            self.energy -= 15
            return True

        return False


class Medic(CrewMember):
    def work(self):
        self.energy = max(0, self.energy - 8)

    def heal(self, member):
        if self.is_alive and member.is_alive and self.energy >= 10:
            member.health = min(100, member.health + 25)
            self.energy -= 10
            return True

        return False
        
