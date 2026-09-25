from crew import Engineer, Medic
from station import Station
from modules import Reactor, LifeSupport, Laboratory


station = Station("Aurora")

engineer = Engineer("Ilya", 100, 100)
medic = Medic("Anna", 100, 100)

reactor = Reactor("Main Reactor")
life_support = LifeSupport("Life Support")
laboratory = Laboratory("Research Lab")

station.add_crew(engineer)
station.add_crew(medic)

station.add_module(reactor)
station.add_module(life_support)
station.add_module(laboratory)



reactor.damage(80)

print("=== REACTOR FAILURE ===")
print(f"Day: {station.day}")
print(f"Station energy: {station.energy}")
print(f"Reactor condition: {reactor.condition}%")


station.next_day()
station.next_day()

print("\n=== TWO DAYS LATER ===")
print(f"Day: {station.day}")
print(f"Station energy: {station.energy}")
print(f"Reactor condition: {reactor.condition}%")


engineer.repair_module(reactor)
engineer.repair_module(reactor)

print("\n=== AFTER REPAIR ===")
print(f"Reactor condition: {reactor.condition}%")
print(f"Engineer energy: {engineer.energy}")


station.next_day()

print("\n=== NEXT DAY ===")
print(f"Day: {station.day}")
print(f"Station energy: {station.energy}")
print(f"Station oxygen: {station.oxygen}")
print(f"Research: {station.research}")
print(f"Reactor condition: {reactor.condition}%")