from station import Station
from modules import Reactor, LifeSupport, Laboratory


station = Station("Aurora")

station.add_module(Reactor("Main Reactor"))
station.add_module(LifeSupport("Life Support"))
station.add_module(Laboratory("Research Lab"))

for _ in range(20):
    station.next_day()

print("=== STATION STATUS ===")
print(f"Day: {station.day}")
print(f"Energy: {station.energy}")
print(f"Oxygen: {station.oxygen}")
print(f"Hull: {station.hull}")
print(f"Research: {station.research}")

print("\n=== EVENT LOG ===")

for event in station.event_log:
    print(event)