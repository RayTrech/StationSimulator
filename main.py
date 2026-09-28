from crew import Engineer, Medic
from modules import Laboratory, LifeSupport, Reactor, StationModule, UpgradeError
from persistence import SaveGameError, load_game, save_game
from station import Station


def create_station():
    station = Station("Аврора")
    station.add_crew(Engineer("Илья", 100, 100))
    station.add_crew(Medic("Анна", 100, 100))
    station.add_module(Reactor("Главный реактор"))
    station.add_module(LifeSupport("Система жизнеобеспечения"))
    station.add_module(Laboratory("Исследовательская лаборатория"))
    return station


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
    print("12. Улучшение модуля")
    print("13. Включить или выключить модуль")
    print("14. Прогноз на следующий день")
    print("0. Выход")


def select_item(items, prompt, missing_message):
    for index, item in enumerate(items, start=1):
        print(f"{index}. {item}")
    try:
        index = int(input(prompt)) - 1
    except ValueError:
        print("Введите целый номер из списка.")
        return None
    if not 0 <= index < len(items):
        print(missing_message)
        return None
    return items[index]


def find_specialist(station, role):
    return next(
        (member for member in station.crew if isinstance(member, role) and member.is_alive),
        None,
    )


def repair_module(station):
    print("\n=== РЕМОНТ МОДУЛЯ ===")
    module = select_item(station.modules, "\nВыберите модуль: ", "Такого модуля нет.")
    if module is None:
        return
    engineer = find_specialist(station, Engineer)
    if engineer is None:
        print("Живой инженер не найден.")
        return
    old_condition = module.condition
    if engineer.repair_module(module):
        print(f"{engineer.name}: отремонтирован модуль «{module.name}».")
        print(f"Состояние: {old_condition}% → {module.condition}%")
        print(f"Энергия инженера: {engineer.energy}")
    else:
        print("Ремонт невозможен: модуль уже исправен или инженеру нужен отдых.")


def heal_crew(station):
    print("\n=== ЛЕЧЕНИЕ ===")
    member = select_item(station.crew, "\nВыберите члена экипажа: ", "Такого члена экипажа нет.")
    if member is None:
        return
    medic = find_specialist(station, Medic)
    if medic is None:
        print("Живой медик не найден.")
        return
    old_health = member.health
    if medic.heal(member):
        print(f"{medic.name}: оказана помощь члену экипажа «{member.name}».")
        print(f"Здоровье: {old_health} → {member.health}")
        print(f"Энергия медика: {medic.energy}")
    else:
        print("Лечение невозможно: пациент погиб, уже здоров или медику нужен отдых.")


def rest_crew(station):
    print("\n=== ОТДЫХ ===")
    member = select_item(station.crew, "\nКто будет отдыхать: ", "Такого члена экипажа нет.")
    if member is None:
        return
    old_energy = member.energy
    if member.rest():
        print(f"{member.name}: отдых завершён.")
        print(f"Энергия: {old_energy} → {member.energy}")
    else:
        print("Отдых невозможен: член экипажа погиб или уже полон энергии.")


def repair_hull(station):
    engineer = find_specialist(station, Engineer)
    if engineer is None:
        print("Живой инженер не найден.")
        return
    old_hull = station.hull
    if engineer.repair_hull(station):
        print(f"{engineer.name}: корпус отремонтирован.")
        print(f"Корпус: {old_hull}% → {station.hull}%")
        print(f"Энергия инженера: {engineer.energy}")
    else:
        print("Ремонт невозможен: корпус исправен, разрушен или инженеру нужен отдых.")


def upgrade_module(station):
    print("\n=== УЛУЧШЕНИЕ МОДУЛЯ ===")
    print(f"Доступно исследований: {station.research}")
    costs = StationModule.upgrade_costs
    print(f"Цена уровней 2 и 3: {costs[0]} и {costs[1]} исследований.")
    print(f"Требуется {StationModule.upgrade_energy_cost} энергии инженера и состояние от 70%.")
    module = select_item(station.modules, "\nВыберите модуль: ", "Такого модуля нет.")
    if module is None:
        return
    try:
        cost = station.upgrade_module(module)
    except UpgradeError as error:
        print(error)
        return
    print(f"Модуль «{module.name}» улучшен до уровня {module.level}.")
    print(f"Потрачено исследований: {cost}; осталось: {station.research}.")
    print("Новая выработка за день: " + str(module.operate()[1]))


def toggle_module(station):
    print("\n=== ПИТАНИЕ МОДУЛЕЙ ===")
    print("Отключённый модуль не расходует энергию и ничего не производит.")
    module = select_item(station.modules, "\nВыберите модуль: ", "Такого модуля нет.")
    if module is None:
        return
    try:
        station.set_module_enabled(module, not module.enabled)
    except ValueError as error:
        print(error)
        return
    action = "включён" if module.enabled else "выключен"
    print(f"Модуль «{module.name}» {action}.")
    if not module.enabled and isinstance(module, (Reactor, LifeSupport)):
        print("Внимание: отключена жизненно важная система. Проверьте прогноз дня.")


def show_forecast(station):
    print("\n=== ПРОГНОЗ НА СЛЕДУЮЩИЙ ДЕНЬ ===")
    print("Без случайных событий; учитываются состояние и питание модулей.")
    forecast = station.forecast_next_day()
    forecast.show_status()
    print("\n=== ПРОГНОЗ ЗДОРОВЬЯ ЭКИПАЖА ===")
    forecast.show_crew()
    if forecast.oxygen == 0 and not station.is_destroyed and not station.mission_completed:
        print("Кислород закончится: живой экипаж потеряет 10 здоровья.")
    if forecast.energy < station.energy:
        print(f"Запас энергии снизится на {station.energy - forecast.energy}.")
    show_game_result(forecast)


def show_game_result(station):
    if station.is_destroyed:
        print("\n=== ИГРА ОКОНЧЕНА ===")
        if station.hull <= 0:
            print(f"Корпус станции «{station.name}» разрушен.")
        else:
            print("Весь экипаж погиб.")
        return True
    if station.mission_completed:
        print("\n=== МИССИЯ ВЫПОЛНЕНА ===")
        print(f"Станция «{station.name}»: день {station.day}.")
        print(f"Исследования: {station.research}/{station.research_goal}")
        print("Научная миссия успешно завершена!")
        return True
    return False


def main():
    station = create_station()
    print("================================")
    print("      СИМУЛЯТОР «АВРОРА»")
    print("================================")
    print("Выживайте, обслуживайте станцию и сохраняйте жизнь экипажа.")
    print(f"Цель миссии: {station.research_goal} единиц исследований.")

    while True:
        show_menu()
        choice = input("\nВыберите действие: ").strip()
        if choice == "1":
            station.show_status()
        elif choice == "2":
            print("\n=== ЭКИПАЖ ===")
            station.show_crew()
        elif choice == "3":
            print("\n=== МОДУЛИ ===")
            station.show_modules()
        elif choice == "4":
            previous_event_count = len(station.event_log)
            station.next_day()
            print(f"\n=== ДЕНЬ {station.day} ===")
            station.show_status()
            if len(station.event_log) > previous_event_count:
                print("\n=== СОБЫТИЕ ===")
                print(station.event_log[-1])
            print("\n=== ЭКИПАЖ ===")
            station.show_crew()
            if show_game_result(station):
                break
        elif choice == "5":
            print("\n=== ЖУРНАЛ СОБЫТИЙ ===")
            if station.event_log:
                for event in station.event_log:
                    print(event)
            else:
                print("Событий пока не было.")
        elif choice == "6":
            repair_module(station)
        elif choice == "7":
            heal_crew(station)
        elif choice == "8":
            rest_crew(station)
        elif choice == "9":
            repair_hull(station)
        elif choice == "10":
            try:
                save_game(station)
                print("\nИгра успешно сохранена.")
            except SaveGameError as error:
                print(f"\n{error}")
        elif choice == "11":
            try:
                station = load_game()
            except SaveGameError as error:
                print(f"\n{error}")
                continue
            print("\nИгра успешно загружена.")
            station.show_status()
            print("\n=== ЭКИПАЖ ===")
            station.show_crew()
            print("\n=== МОДУЛИ ===")
            station.show_modules()
            if show_game_result(station):
                break
        elif choice == "12":
            upgrade_module(station)
        elif choice == "13":
            toggle_module(station)
        elif choice == "14":
            show_forecast(station)
        elif choice == "0":
            print("\nРабота симулятора завершена.")
            break
        else:
            print("\nНеизвестная команда.")


if __name__ == "__main__":
    main()
