import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from crew import CrewMember, Engineer, Medic
from events import (
    MedicalEmergencyEvent,
    MeteorEvent,
    ModuleFailureEvent,
    OxygenLeakEvent,
    ScientificBreakthroughEvent,
    SolarFlareEvent,
)
import main
from modules import Laboratory, LifeSupport, Reactor
from persistence import SaveGameError, load_game, save_game
from station import Station


class StationTests(unittest.TestCase):
    def setUp(self):
        self.station = main.create_station()
        self.no_event = patch("station.random.random", return_value=1.0)
        self.no_event.start()
        self.addCleanup(self.no_event.stop)

    def test_healthy_station_wins_after_25_turns(self):
        for _ in range(25):
            self.assertTrue(self.station.next_day())
        self.assertTrue(self.station.mission_completed)
        self.assertEqual(self.station.research, 200)
        self.assertEqual(self.station.day, 26)
        self.assertEqual(self.station.energy, 65)
        self.assertEqual(self.station.oxygen, 100)
        before = self.station.to_dict()
        self.assertFalse(self.station.next_day())
        self.assertEqual(self.station.to_dict(), before)

    def test_hull_destruction_stops_game_even_with_completed_research(self):
        self.station.hull = 20
        self.station.research = 200
        MeteorEvent().apply(self.station)
        self.assertTrue(self.station.is_destroyed)
        self.assertFalse(self.station.mission_completed)
        self.assertFalse(self.station.next_day())

    def test_dead_crew_stops_game(self):
        for member in self.station.crew:
            member.take_damage(100)
        self.assertTrue(self.station.is_destroyed)
        self.assertFalse(self.station.next_day())

    def test_fatal_event_on_final_research_day_overrides_victory(self):
        self.station.research = 192
        self.station.hull = 20
        with patch("station.random.random", return_value=0), patch(
            "station.random.choice", return_value=MeteorEvent
        ):
            self.assertTrue(self.station.next_day())
        self.assertEqual(self.station.research, 200)
        self.assertTrue(self.station.is_destroyed)
        self.assertFalse(self.station.mission_completed)

    def test_suffocation_on_final_research_day_overrides_victory(self):
        self.station.research = 192
        self.station.oxygen = 0
        self.station.modules[1].condition = 0
        for member in self.station.crew:
            member.health = 10
        self.assertTrue(self.station.next_day())
        self.assertEqual(self.station.research, 200)
        self.assertTrue(self.station.is_destroyed)
        self.assertFalse(self.station.mission_completed)

    def test_one_survivor_can_continue(self):
        self.station.crew[0].take_damage(100)
        self.assertFalse(self.station.is_destroyed)
        self.assertTrue(self.station.next_day())

    def test_zero_oxygen_damages_then_kills_crew(self):
        self.station.oxygen = 0
        self.station.modules[1].condition = 0
        self.station.next_day()
        self.assertEqual([member.health for member in self.station.crew], [90, 90])
        for _ in range(9):
            self.station.next_day()
        self.assertTrue(self.station.is_destroyed)
        self.assertFalse(self.station.next_day())

    def test_life_support_can_restore_oxygen_before_suffocation(self):
        self.station.oxygen = 0
        self.station.next_day()
        self.assertEqual(self.station.oxygen, 20)
        self.assertEqual([member.health for member in self.station.crew], [100, 100])

    def test_broken_reactor_exhausts_reserve_and_stops_modules(self):
        self.station.modules[0].condition = 0
        self.station.next_day()
        self.assertEqual(self.station.energy, 45)
        self.assertEqual(self.station.research, 8)
        self.station.next_day()
        self.assertEqual(self.station.energy, 5)
        self.assertEqual(self.station.research, 8)
        self.station.next_day()
        self.assertEqual(self.station.energy, 0)
        self.assertEqual(self.station.oxygen, 85)

    def test_life_support_has_priority_independent_of_list_order(self):
        self.station.modules.reverse()
        self.station.modules[-1].condition = 0
        self.station.energy = 40
        self.station.oxygen = 50
        self.station.next_day()
        self.assertEqual(self.station.oxygen, 55)
        self.assertEqual(self.station.energy, 0)
        self.assertEqual(self.station.research, 0)

    def test_broken_powered_modules_do_not_consume_energy(self):
        self.station.modules[1].condition = 0
        self.station.modules[2].condition = 0
        self.station.next_day()
        self.assertEqual(self.station.energy, 100)
        self.assertEqual(self.station.oxygen, 85)
        self.assertEqual(self.station.research, 0)

    def test_event_log_uses_displayed_day(self):
        with patch("station.random.random", return_value=0), patch(
            "station.random.choice", return_value=MeteorEvent
        ):
            self.station.next_day()
        self.assertEqual(self.station.day, 2)
        self.assertEqual(self.station.hull, 80)
        self.assertTrue(self.station.event_log[-1].startswith("День 2: "))

    def test_output_at_condition_boundaries(self):
        for module, resource, full, half in (
            (Reactor("Реактор"), "energy", 55, 27),
            (LifeSupport("Жизнеобеспечение"), "oxygen", 20, 10),
            (Laboratory("Лаборатория"), "research", 8, 4),
        ):
            for condition, expected in ((0, 0), (29, 0), (30, half), (69, half), (70, full), (100, full)):
                with self.subTest(module=type(module).__name__, condition=condition):
                    module.condition = condition
                    self.assertEqual(module.operate(), (resource, expected))


class CrewTests(unittest.TestCase):
    def setUp(self):
        self.station = main.create_station()
        self.engineer, self.medic = self.station.crew

    def test_module_repair_cost_and_limit(self):
        module = self.station.modules[0]
        module.condition = 90
        self.assertTrue(self.engineer.repair_module(module))
        self.assertEqual((module.condition, self.engineer.energy), (100, 85))
        self.assertFalse(self.engineer.repair_module(module))
        self.assertEqual(self.engineer.energy, 85)
        module.condition = 0
        self.engineer.energy = 15
        self.assertTrue(self.engineer.repair_module(module))
        self.assertEqual((module.condition, self.engineer.energy), (30, 0))
        self.assertFalse(self.engineer.repair_module(module))

    def test_hull_repair_cannot_resurrect_destroyed_station(self):
        self.station.hull = 90
        self.assertTrue(self.engineer.repair_hull(self.station))
        self.assertEqual((self.station.hull, self.engineer.energy), (100, 80))
        self.assertFalse(self.engineer.repair_hull(self.station))
        self.station.hull = 0
        self.assertFalse(self.engineer.repair_hull(self.station))
        self.assertEqual(self.station.hull, 0)

    def test_healing_cost_limit_and_dead_patient(self):
        self.engineer.health = 90
        self.assertTrue(self.medic.heal(self.engineer))
        self.assertEqual((self.engineer.health, self.medic.energy), (100, 90))
        self.assertFalse(self.medic.heal(self.engineer))
        self.engineer.health = 0
        self.assertFalse(self.medic.heal(self.engineer))
        self.assertEqual((self.engineer.health, self.medic.energy), (0, 90))

    def test_medic_can_heal_self_with_exact_energy_cost(self):
        self.medic.health = 60
        self.medic.energy = 10
        self.assertTrue(self.medic.heal(self.medic))
        self.assertEqual((self.medic.health, self.medic.energy), (85, 0))
        self.assertFalse(self.medic.heal(self.medic))

    def test_dead_specialists_cannot_act(self):
        self.engineer.health = 0
        self.medic.health = 0
        self.station.hull = 50
        self.station.modules[0].condition = 0
        self.assertFalse(self.engineer.repair_module(self.station.modules[0]))
        self.assertFalse(self.engineer.repair_hull(self.station))
        self.assertFalse(self.medic.heal(CrewMember("Пациент", 50, 100)))
        self.assertFalse(self.engineer.rest())

    def test_rest_restores_energy_without_exceeding_limit(self):
        self.engineer.energy = 90
        self.assertTrue(self.engineer.rest())
        self.assertEqual(self.engineer.energy, 100)
        self.assertFalse(self.engineer.rest())

    def test_negative_damage_and_repair_are_rejected(self):
        for action in (
            self.engineer.take_damage,
            self.station.modules[0].damage,
            self.station.modules[0].repair,
        ):
            with self.assertRaises(ValueError):
                action(-10)


class EventTests(unittest.TestCase):
    def setUp(self):
        self.station = main.create_station()

    def test_meteor_and_oxygen_leak_clamp_to_zero(self):
        self.station.hull = 10
        self.station.oxygen = 10
        MeteorEvent().apply(self.station)
        OxygenLeakEvent().apply(self.station)
        self.assertEqual((self.station.hull, self.station.oxygen), (0, 0))

    def test_module_failure_damages_selected_module(self):
        module = self.station.modules[0]
        with patch("events.random.choice", return_value=module):
            message = ModuleFailureEvent().apply(self.station)
        self.assertEqual(module.condition, 60)
        self.assertIn(module.name, message)

    def test_solar_flare_damages_reactor_and_drains_energy(self):
        self.station.energy = 20
        SolarFlareEvent().apply(self.station)
        self.assertEqual(self.station.energy, 0)
        self.assertEqual(self.station.modules[0].condition, 80)

    def test_medical_emergency_targets_living_crew_only(self):
        self.station.crew[0].health = 0
        message = MedicalEmergencyEvent().apply(self.station)
        self.assertEqual(self.station.crew[1].health, 70)
        self.assertIn("Анна", message)

    def test_breakthrough_requires_operational_laboratory(self):
        event = ScientificBreakthroughEvent()
        event.apply(self.station)
        self.assertEqual(self.station.research, 15)
        self.station.modules[2].condition = 29
        self.assertIn("отложен", event.apply(self.station))
        self.assertEqual(self.station.research, 15)

    def test_events_handle_missing_targets(self):
        station = Station("Пустая станция")
        for event in (ModuleFailureEvent(), SolarFlareEvent(), MedicalEmergencyEvent(), ScientificBreakthroughEvent()):
            with self.subTest(event=event.name):
                self.assertIsInstance(event.apply(station), str)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.station = main.create_station()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "save.json"

    def test_round_trip_preserves_every_field_and_subclass(self):
        self.station.day = 7
        self.station.research = 48
        self.station.hull = 80
        self.station.energy = 35
        self.station.oxygen = 55
        self.station.crew[0].health = 70
        self.station.crew[1].energy = 40
        self.station.modules[0].condition = 60
        self.station.event_log = ["День 6: Удар метеорита!", "День 7: Утечка кислорода!"]
        save_game(self.station, self.path)
        restored = load_game(self.path)
        self.assertEqual(restored.to_dict(), self.station.to_dict())
        self.assertIsInstance(restored.crew[0], Engineer)
        self.assertIsInstance(restored.crew[1], Medic)
        self.assertEqual([type(module) for module in restored.modules], [Reactor, LifeSupport, Laboratory])
        self.assertIn("Удар метеорита", self.path.read_text(encoding="utf-8"))
        with patch("station.random.random", return_value=1):
            self.station.next_day()
            restored.next_day()
        self.assertEqual(restored.to_dict(), self.station.to_dict())

    def test_old_save_without_log_loads(self):
        data = self.station.to_dict()
        del data["event_log"]
        self.path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(load_game(self.path).event_log, [])

    def test_missing_file_has_friendly_error(self):
        with self.assertRaisesRegex(SaveGameError, "не найден"):
            load_game(self.path)

    def test_corrupt_json_and_encoding_have_friendly_errors(self):
        for content in (b"", b"{broken", b"\xff\xfe", b"[", b"[" * 2000):
            with self.subTest(content=content[:20]):
                self.path.write_bytes(content)
                with self.assertRaisesRegex(SaveGameError, "повреждён"):
                    load_game(self.path)

    def test_invalid_save_structure_is_rejected(self):
        valid = self.station.to_dict()
        invalid = [None, [], {}, {**valid, "day": True}, {**valid, "hull": -1},
                   {**valid, "energy": 101}, {**valid, "oxygen": "100"},
                   {**valid, "research": 1.5}, {**valid, "research_goal": 0},
                   {**valid, "crew": None}, {**valid, "modules": {}},
                   {**valid, "event_log": [15]}, {**valid, "name": " "}]
        for key, field, value in (
            ("crew", "type", "Unknown"), ("crew", "type", []),
            ("crew", "health", 101), ("crew", "energy", False),
            ("modules", "type", "Unknown"), ("modules", "condition", -1),
        ):
            data = copy.deepcopy(valid)
            data[key][0][field] = value
            invalid.append(data)
        invalid.append({**valid, "crew": [None]})
        invalid.append({**valid, "modules": [{}]})
        for data in invalid:
            with self.subTest(data=data):
                self.path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(SaveGameError, "повреждён"):
                    load_game(self.path)

    def test_bom_is_supported(self):
        self.path.write_text(json.dumps(self.station.to_dict()), encoding="utf-8-sig")
        self.assertEqual(load_game(self.path).to_dict(), self.station.to_dict())

    def test_failed_write_preserves_previous_save_and_removes_temporary_file(self):
        save_game(self.station, self.path)
        original = self.path.read_bytes()
        self.station.research = 100
        for operation in ("persistence.json.dump", "persistence.os.replace"):
            with self.subTest(operation=operation), patch(operation, side_effect=OSError("Нет доступа")):
                with self.assertRaises(SaveGameError):
                    save_game(self.station, self.path)
            self.assertEqual(self.path.read_bytes(), original)
            self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_file_access_errors_are_wrapped(self):
        with patch("pathlib.Path.open", side_effect=PermissionError):
            with self.assertRaisesRegex(SaveGameError, "прочитать"):
                load_game(self.path)
        with self.assertRaisesRegex(SaveGameError, "сохранить"):
            save_game(self.station, self.path.parent / "missing" / "save.json")


class ConsoleTests(unittest.TestCase):
    def run_main(self, station, commands):
        output = io.StringIO()
        with patch("main.create_station", return_value=station), patch(
            "builtins.input", side_effect=commands
        ), patch("station.random.random", return_value=1), redirect_stdout(output):
            main.main()
        return output.getvalue()

    def test_corrupt_load_keeps_current_game_and_menu_alive(self):
        station = main.create_station()
        station.research = 40
        with patch("main.load_game", side_effect=SaveGameError("Файл сохранения повреждён.")):
            output = self.run_main(station, ["5", "2", "0", "4", "0"])
        self.assertIn("повреждён", output)
        self.assertIn("Работа симулятора завершена", output)
        self.assertEqual(station.research, 48)

    def test_menu_repairs_heals_rests_saves_and_loads(self):
        station = main.create_station()
        station.modules[0].condition = 40
        station.crew[0].energy = 50
        station.crew[1].health = 60
        station.hull = 60
        station.event_log = ["День 1: Начало миссии."]
        restored = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"

            def read_save():
                loaded = load_game(path)
                restored.append(loaded)
                return loaded

            with patch("main.save_game", side_effect=lambda current: save_game(current, path)), patch(
                "main.load_game", side_effect=read_save
            ):
                output = self.run_main(station, [
                    "3", "2", "1", "0",  # Ремонт модуля.
                    "2", "2", "2", "3", "1", "0",  # Лечение и отдых.
                    "1", "4", "0",  # Ремонт корпуса.
                    "5", "1", "0", "4",  # Сохранение и переход дня.
                    "5", "2", "0", "1", "3", "0", "0",  # Загрузка и журнал.
                ])
        self.assertEqual(restored[0].day, 1)
        self.assertEqual(restored[0].hull, 85)
        self.assertEqual(restored[0].modules[0].condition, 70)
        self.assertEqual(restored[0].crew[0].energy, 35)
        self.assertEqual(restored[0].crew[1].health, 85)
        self.assertIn("Игра успешно сохранена", output)
        self.assertIn("Игра успешно загружена", output)
        self.assertIn("День 1: Начало миссии.", output)
        for english in ("Engineer", "Medic", "Condition", "Meteor impact", "Health", "Energy"):
            self.assertNotIn(english, output)

    def test_invalid_selection_does_not_crash(self):
        for choice in ("текст", "²", "0", "-1", "99", ""):
            with self.subTest(choice=choice):
                self.run_main(main.create_station(), ["3", "2", choice, "0", "0"])

    def test_browsing_sections_and_returning_keeps_station_unchanged(self):
        station = main.create_station()
        before = station.to_dict()
        output = self.run_main(station, [
            "1", "1", "2", "3", "0",  # Состояние, прогноз, журнал.
            "2", "1", "0", "3", "1", "0", "5", "0", "0",
        ])
        self.assertIn("0. Назад", output)
        self.assertIn("Событий пока не было", output)
        self.assertEqual(station.to_dict(), before)

    def test_unknown_commands_in_each_section_allow_return_and_next_day(self):
        station = main.create_station()
        output = self.run_main(station, [
            "99", "1", "99", "0", "2", "текст", "0",
            "3", "-1", "0", "5", "ошибка", "0", "4", "0",
        ])
        self.assertEqual(output.count("Неизвестная команда"), 5)
        self.assertEqual((station.day, station.research), (2, 8))

    def test_failed_save_keeps_submenu_and_current_game_alive(self):
        station = main.create_station()
        with patch("main.save_game", side_effect=SaveGameError("Нет доступа к файлу.")):
            output = self.run_main(station, ["5", "1", "0", "4", "0"])
        self.assertIn("Нет доступа к файлу", output)
        self.assertEqual((station.day, station.research), (2, 8))

    def test_loaded_station_is_used_for_actions_in_current_and_other_sections(self):
        station = main.create_station()
        before = station.to_dict()
        restored = main.create_station()
        restored.day, restored.research = 7, 80
        restored.modules[2].enabled = False
        restored_before = restored.to_dict()
        saved = []
        with patch("main.load_game", return_value=restored), patch(
            "main.save_game", side_effect=lambda current: saved.append(current.to_dict())
        ):
            self.run_main(station, [
                "5", "2", "1", "0",  # Загрузить и сохранить в том же разделе.
                "3", "4", "3", "0", "4",  # Включить лабораторию и перейти к новому дню.
                "5", "1", "0", "0",
            ])
        self.assertEqual(saved[0], restored_before)
        self.assertEqual(saved[1], restored.to_dict())
        self.assertEqual((restored.day, restored.research), (8, 88))
        self.assertTrue(restored.modules[2].enabled)
        self.assertEqual(station.to_dict(), before)

    def test_victory_and_defeat_are_displayed(self):
        for reason in ("victory", "hull", "crew"):
            with self.subTest(reason=reason):
                station = main.create_station()
                if reason == "victory":
                    station.research = 192
                elif reason == "hull":
                    station.hull = 0
                    station.research = 200
                else:
                    for member in station.crew:
                        member.health = 0
                output = self.run_main(station, ["4"])
                if reason == "victory":
                    self.assertIn("МИССИЯ ВЫПОЛНЕНА", output)
                else:
                    self.assertIn("ИГРА ОКОНЧЕНА", output)
                    self.assertNotIn("МИССИЯ ВЫПОЛНЕНА", output)

    def test_loading_finished_game_displays_result_immediately(self):
        station = main.create_station()
        station.research = 200
        with patch("main.load_game", return_value=station):
            output = self.run_main(main.create_station(), ["5", "2"])
        self.assertIn("МИССИЯ ВЫПОЛНЕНА", output)


if __name__ == "__main__":
    unittest.main()
