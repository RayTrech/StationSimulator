from crew import Engineer, Medic
from station import Station
from modules import Reactor, LifeSupport, Laboratory


def show_menu():
    print("\n=== AURORA STATION ===")
    print("1. Station status")
    print("2. Show crew")
    print("3. Show modules")
    print("4. Next day")
    print("5. Event log")
    print("6. Repair module")
    print("7. Heal crew member")
    print("8. Rest crew member")
    print("0. Exit")


def main():
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

    print("================================")
    print("   AURORA STATION SIMULATOR")
    print("================================")
    print("Survive, maintain the station")
    print("and keep the crew alive.")

    while True:
        show_menu()

        choice = input("\nChoose action: ")

        if choice == "1":
            station.show_status()

        elif choice == "2":
            print("\n=== CREW ===")
            station.show_crew()

        elif choice == "3":
            print("\n=== MODULES ===")
            station.show_modules()


        elif choice == "4":
            previous_event_count = len(station.event_log)

            result = station.next_day()

            if result:
                print(f"\n=== DAY {station.day} ===")
                station.show_status()

                # Если за прошедший день произошло событие,
                # сразу показываем его игроку
                if len(station.event_log) > previous_event_count:
                    print("\n=== EVENT ===")
                    print(station.event_log[-1])

                # Показываем состояние экипажа
                print("\n=== CREW ===")
                station.show_crew()

                # Если станция была уничтожена именно в этот день
                if station.is_destroyed:
                    print("\n=== GAME OVER ===")
                    print("Aurora station has been destroyed.")
                    break

            else:
                print("\n=== GAME OVER ===")
                print("Aurora station has been destroyed.")
                break


        elif choice == "5":
            print("\n=== EVENT LOG ===")

            if not station.event_log:
                print("No events yet.")
            else:
                for event in station.event_log:
                    print(event)


        elif choice == "6":
            print("\n=== REPAIR MODULE ===")

            for index, module in enumerate(station.modules, start=1):
                print(f"{index}. {module}")

            module_choice = input("\nChoose module: ")

            if module_choice.isdigit():
                index = int(module_choice) - 1

                if 0 <= index < len(station.modules):
                    module = station.modules[index]

                    old_condition = module.condition

                    success = engineer.repair_module(module)

                    if success:
                        print(f"\n{engineer.name} repaired {module.name}.")
                        print(
                            f"Condition: "
                            f"{old_condition}% -> {module.condition}%"
                        )
                        print(
                            f"Engineer energy: "
                            f"{engineer.energy}"
                        )
                    else:
                        print("\nEngineer cannot repair this module.")

                else:
                    print("\nInvalid module.")
            else:
                print("\nInvalid module.")


        elif choice == "7":
            print("\n=== HEAL CREW MEMBER ===")

            for index, member in enumerate(station.crew, start=1):
                print(f"{index}. {member}")

            member_choice = input("\nChoose crew member: ")

            if member_choice.isdigit():
                index = int(member_choice) - 1

                if 0 <= index < len(station.crew):
                    member = station.crew[index]

                    old_health = member.health

                    success = medic.heal(member)

                    if success:
                        print(
                            f"\n{medic.name} healed "
                            f"{member.name}."
                        )
                        print(
                            f"Health: "
                            f"{old_health} -> {member.health}"
                        )
                        print(
                            f"Medic energy: "
                            f"{medic.energy}"
                        )
                    else:
                        print(
                            "\nMedic cannot heal "
                            "this crew member."
                        )

                else:
                    print("\nInvalid crew member.")
            else:
                print("\nInvalid crew member.")


        elif choice == "8":
            print("\n=== REST ===")

            for index, member in enumerate(station.crew, start=1):
                print(f"{index}. {member}")

            member_choice = input(
                "\nChoose crew member to rest: "
            )

            if member_choice.isdigit():
                index = int(member_choice) - 1

                if 0 <= index < len(station.crew):
                    member = station.crew[index]

                    if not member.is_alive:
                        print(
                            "\nThis crew member "
                            "cannot rest."
                        )

                    elif member.energy >= 100:
                        print(
                            f"\n{member.name} already "
                            "has full energy."
                        )

                    else:
                        old_energy = member.energy
                        member.rest()

                        print(
                            f"\n{member.name} rested."
                        )
                        print(
                            f"Energy: "
                            f"{old_energy} -> "
                            f"{member.energy}"
                        )

                else:
                    print("\nInvalid crew member.")
            else:
                print("\nInvalid crew member.")

        elif choice == "0":
            print("\nSimulation terminated.")
            break

        else:
            print("\nUnknown command.")


if __name__ == "__main__":
    main()