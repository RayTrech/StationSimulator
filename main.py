import json

from crew import Engineer, Medic
from station import Station
from modules import Reactor, LifeSupport, Laboratory


def show_menu():
    print("\n=== СТАНЦИЯ «АВРОРА» ===")
    print("1. Состояние станции")
    print("2. Экипаж")
    print("3. Модули")
    print("4. Следующий день")
    print("5. Журнал событий")
    print("6. Ремонт модуля")
    print("7. Лечение члена экипажа")
    print("8. Отдых члена экипажа")
    print("9. Ремонт корпуса")
    print("10. Сохранить игру")
    print("11. Загрузить игру")
    print("0. Выход")

def main():
    station = Station("Аврора")

    engineer = Engineer("Илья", 100, 100)
    medic = Medic("Анна", 100, 100)

    reactor = Reactor("Главный реактор")
    life_support = LifeSupport(
        "Система жизнеобеспечения"
    )
    laboratory = Laboratory(
        "Исследовательская лаборатория"
    )

    station.add_crew(engineer)
    station.add_crew(medic)

    station.add_module(reactor)
    station.add_module(life_support)
    station.add_module(laboratory)

    print("================================")
    print("      СИМУЛЯТОР «АВРОРА»")
    print("================================")
    print("Выживайте, обслуживайте станцию")
    print("и сохраняйте жизнь экипажа.")

    while True:
        show_menu()

        choice = input("\nВыберите действие: ")

        if choice == "1":
            station.show_status()

        elif choice == "2":
            print("\n=== ЭКИПАЖ ===")
            station.show_crew()

        elif choice == "3":
            print("\n=== МОДУЛИ ===")
            station.show_modules()

        elif choice == "4":
            previous_event_count = len(
                station.event_log
            )

            result = station.next_day()

            if result:
                print(
                    f"\n=== ДЕНЬ {station.day} ==="
                )

                station.show_status()

                # Если произошло новое событие
                if (
                    len(station.event_log)
                    > previous_event_count
                ):
                    print("\n=== СОБЫТИЕ ===")
                    print(station.event_log[-1])

                # Показываем состояние экипажа
                print("\n=== ЭКИПАЖ ===")
                station.show_crew()

                # Проверяем выполнение миссии
                if station.mission_completed:
                    print(
                        "\n=============================="
                    )
                    print(
                        "        МИССИЯ ВЫПОЛНЕНА"
                    )
                    print(
                        "=============================="
                    )
                    print(
                        f"Станция «{station.name}» "
                        f"продержалась {station.day} дней."
                    )
                    print(
                        f"Исследования: "
                        f"{station.research}/"
                        f"{station.research_goal}"
                    )
                    print(
                        "Научная миссия успешно "
                        "завершена!"
                    )

                    break

                # Проверяем уничтожение станции
                if station.is_destroyed:
                    print("\n=== ИГРА ОКОНЧЕНА ===")
                    print(
                        f"Станция «{station.name}» "
                        "уничтожена."
                    )

                    break

            else:
                print("\n=== ИГРА ОКОНЧЕНА ===")
                print(
                    f"Станция «{station.name}» "
                    "уничтожена."
                )

                break

        elif choice == "5":
            print("\n=== ЖУРНАЛ СОБЫТИЙ ===")

            if not station.event_log:
                print("Событий пока не было.")

            else:
                for event in station.event_log:
                    print(event)

        elif choice == "6":
            print("\n=== РЕМОНТ МОДУЛЯ ===")

            for index, module in enumerate(
                station.modules,
                start=1
            ):
                print(f"{index}. {module}")

            module_choice = input(
                "\nВыберите модуль: "
            )

            if module_choice.isdigit():
                index = int(module_choice) - 1

                if 0 <= index < len(
                    station.modules
                ):
                    module = station.modules[index]

                    old_condition = (
                        module.condition
                    )

                    if engineer is None:
                        print(
                            "\nИнженер не найден."
                        )

                    else:
                        success = (
                            engineer.repair_module(
                                module
                            )
                        )

                        if success:
                            print(
                                f"\n{engineer.name} "
                                f"отремонтировал модуль "
                                f"«{module.name}»."
                            )

                            print(
                                f"Состояние: "
                                f"{old_condition}% "
                                f"-> "
                                f"{module.condition}%"
                            )

                            print(
                                f"Энергия инженера: "
                                f"{engineer.energy}"
                            )

                        else:
                            print(
                                "\nИнженер не может "
                                "отремонтировать этот "
                                "модуль."
                            )

                else:
                    print(
                        "\nТакого модуля нет."
                    )

            else:
                print(
                    "\nВведите номер модуля."
                )

        elif choice == "7":
            print("\n=== ЛЕЧЕНИЕ ===")

            for index, member in enumerate(
                station.crew,
                start=1
            ):
                print(f"{index}. {member}")

            member_choice = input(
                "\nВыберите члена экипажа: "
            )

            if member_choice.isdigit():
                index = int(member_choice) - 1

                if 0 <= index < len(
                    station.crew
                ):
                    member = station.crew[index]

                    old_health = member.health

                    if medic is None:
                        print(
                            "\nМедик не найден."
                        )

                    else:
                        success = medic.heal(
                            member
                        )

                        if success:
                            print(
                                f"\n{medic.name} "
                                f"вылечила "
                                f"{member.name}."
                            )

                            print(
                                f"Здоровье: "
                                f"{old_health} "
                                f"-> "
                                f"{member.health}"
                            )

                            print(
                                f"Энергия медика: "
                                f"{medic.energy}"
                            )

                        else:
                            print(
                                "\nМедик не может "
                                "вылечить этого "
                                "члена экипажа."
                            )

                else:
                    print(
                        "\nТакого члена "
                        "экипажа нет."
                    )

            else:
                print(
                    "\nВведите номер "
                    "члена экипажа."
                )

        elif choice == "8":
            print("\n=== ОТДЫХ ===")

            for index, member in enumerate(
                station.crew,
                start=1
            ):
                print(f"{index}. {member}")

            member_choice = input(
                "\nКто будет отдыхать: "
            )

            if member_choice.isdigit():
                index = int(member_choice) - 1

                if 0 <= index < len(
                    station.crew
                ):
                    member = station.crew[index]

                    if not member.is_alive:
                        print(
                            "\nЭтот член экипажа "
                            "не может отдыхать."
                        )

                    elif member.energy >= 100:
                        print(
                            f"\nУ {member.name} "
                            "уже максимальный "
                            "запас энергии."
                        )

                    else:
                        old_energy = member.energy

                        member.rest()

                        print(
                            f"\n{member.name} "
                            "отдохнул."
                        )

                        print(
                            f"Энергия: "
                            f"{old_energy} "
                            f"-> "
                            f"{member.energy}"
                        )

                else:
                    print(
                        "\nТакого члена "
                        "экипажа нет."
                    )

            else:
                print(
                    "\nВведите номер "
                    "члена экипажа."
                )

        elif choice == "9":
            old_hull = station.hull

            if engineer is None:
                print(
                    "\nИнженер не найден."
                )

            else:
                success = engineer.repair_hull(
                    station
                )

                if success:
                    print(
                        f"\n{engineer.name} "
                        "отремонтировал корпус."
                    )

                    print(
                        f"Корпус: "
                        f"{old_hull}% "
                        f"-> "
                        f"{station.hull}%"
                    )

                    print(
                        f"Энергия инженера: "
                        f"{engineer.energy}"
                    )

                else:
                    print(
                        "\nИнженер не может "
                        "отремонтировать корпус."
                    )

        
        elif choice == "10":
            with open(
                "save.json",
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    station.to_dict(),
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            print(
                "\nИгра успешно сохранена."
            )

        # -----------------------------------
        # 11. ЗАГРУЗКА ИГРЫ
        # -----------------------------------

        elif choice == "11":
            try:
                with open(
                    "save.json",
                    "r",
                    encoding="utf-8"
                ) as file:
                    data = json.load(file)

                station = Station.from_dict(
                    data
                )

                engineer = next(
                    (
                        member
                        for member in station.crew
                        if isinstance(
                            member,
                            Engineer
                        )
                    ),
                    None
                )

                medic = next(
                    (
                        member
                        for member in station.crew
                        if isinstance(
                            member,
                            Medic
                        )
                    ),
                    None
                )

                print(
                    "\nИгра успешно загружена."
                )

                station.show_status()

                print("\n=== ЭКИПАЖ ===")
                station.show_crew()

                print("\n=== МОДУЛИ ===")
                station.show_modules()

            except FileNotFoundError:
                print(
                    "\nФайл сохранения "
                    "не найден."
                )

        elif choice == "0":
            print(
                "\nРабота симулятора завершена."
            )

            break

        else:
            print(
                "\nНеизвестная команда."
            )


if __name__ == "__main__":
    main()