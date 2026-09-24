from station import Station
from modules import Reactor, LifeSupport, Laboratory


station = Station("Aurora")

reactor = Reactor("Main Reactor")
life_support = LifeSupport("Life Support")
laboratory = Laboratory("Research Lab")

station.add_module(reactor)
station.add_module(life_support)
station.add_module(laboratory)

# Повреждаем реактор — теперь он производит только 25 энергии
reactor.damage(80)

for _ in range(5):
    print(f"\n=== DAY {station.day} ===")
    print(f"Energy: {station.energy}")
    print(f"Oxygen: {station.oxygen}")
    print(f"Research: {station.research}")

    station.next_day()