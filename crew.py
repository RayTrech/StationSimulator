class CrewMember:
    role = "Член экипажа"

    def __init__(self, name, health, energy):
        self.name = name
        self.health = health
        self.energy = energy

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if type(value) is not int or not 0 <= value <= 100:
            raise ValueError("Здоровье должно быть целым числом от 0 до 100.")
        self._health = value

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        if type(value) is not int or not 0 <= value <= 100:
            raise ValueError("Энергия должна быть целым числом от 0 до 100.")
        self._energy = value

    @property
    def is_alive(self):
        return self.health > 0

    def rest(self):
        if not self.is_alive or self.energy == 100:
            return False
        self.energy = min(100, self.energy + 20)
        return True

    def take_damage(self, amount):
        if type(amount) is not int or amount < 0:
            raise ValueError("Урон должен быть неотрицательным целым числом.")
        self.health = max(0, self.health - amount)

    def __str__(self):
        return (
            f"{self.role} {self.name} | "
            f"Здоровье: {self.health} | Энергия: {self.energy}"
        )

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "health": self.health,
            "energy": self.energy,
        }


class Engineer(CrewMember):
    role = "Инженер"

    def repair_module(self, module):
        if not self.is_alive or self.energy < 15 or module.condition == 100:
            return False
        module.repair(30)
        self.energy -= 15
        return True

    def repair_hull(self, station):
        if not self.is_alive or self.energy < 20 or not 0 < station.hull < 100:
            return False
        station.hull = min(100, station.hull + 25)
        self.energy -= 20
        return True


class Medic(CrewMember):
    role = "Медик"

    def heal(self, member):
        if (
            not self.is_alive
            or not member.is_alive
            or self.energy < 10
            or member.health == 100
        ):
            return False
        member.health = min(100, member.health + 25)
        self.energy -= 10
        return True
