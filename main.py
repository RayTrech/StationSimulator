from crew import Engineer, Medic
from station import Station


station = Station("Aurora")

engineer = Engineer("Ilya", 100, 100)
medic = Medic("Anna", 100, 100)

station.add_crew(engineer)
station.add_crew(medic)


print("=== START ===")
print(f"Destroyed: {station.is_destroyed}")
print(f"Day: {station.day}")


# Уничтожаем корпус
station.hull = 0

print("\n=== HULL DESTROYED ===")
print(f"Hull: {station.hull}")
print(f"Destroyed: {station.is_destroyed}")


# Пытаемся запустить следующий день
result = station.next_day()

print("\n=== TRY NEXT DAY ===")
print(f"Next day result: {result}")
print(f"Day: {station.day}")