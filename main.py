from crew import Engineer, Medic
from station import Station


station = Station("Aurora")

engineer = Engineer("Ilya", 100, 100)
medic = Medic("Anna", 100, 100)

station.add_crew(engineer)
station.add_crew(medic)

engineer.work()

station.show_crew()