"""Воспроизводимые партии с обслуживанием и без него, без внешних пакетов."""

import random
import statistics

from main import create_station


def play(seed, maintenance, turn_limit=120):
    random.seed(seed)
    station = create_station()
    engineer, medic = station.crew
    repairs = 0
    turns = 0
    while not station.is_destroyed and not station.mission_completed and turns < turn_limit:
        if maintenance:
            for module in station.modules:
                if module.condition < 70:
                    while engineer.is_alive and engineer.energy < 15:
                        engineer.rest()
                    repairs += engineer.repair_module(module)
            if station.hull <= 60:
                while engineer.is_alive and engineer.energy < 20:
                    engineer.rest()
                repairs += engineer.repair_hull(station)
            for member in station.crew:
                if member.is_alive and member.health <= 70:
                    while medic.is_alive and medic.energy < 10:
                        medic.rest()
                    medic.heal(member)
        station.next_day()
        turns += 1
    return station.mission_completed, turns, repairs


def simulate(games=500):
    for maintenance in (False, True):
        results = [play(seed, maintenance) for seed in range(games)]
        winning_turns = [turns for won, turns, _ in results if won]
        strategy = "С обслуживанием" if maintenance else "Без обслуживания"
        median = statistics.median(winning_turns) if winning_turns else "нет побед"
        repairs = statistics.mean(count for _, _, count in results)
        print(f"{strategy}: победы {len(winning_turns)}/{games}; "
              f"медиана переходов дня до победы: {median}; ремонтов в среднем: {repairs:.2f}")


if __name__ == "__main__":
    simulate()
