from crew import Engineer, Medic


engineer = Engineer("Ilya", 100, 100)
medic = Medic("Anna", 100, 100)

print(engineer)
print(medic)

engineer.work()
medic.work()

print("\nAfter work:")
print(engineer)
print(medic)

engineer.rest()
medic.rest()

print("\nAfter rest:")
print(engineer)
print(medic)