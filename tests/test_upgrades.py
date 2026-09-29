from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main
from modules import Laboratory, LifeSupport, Reactor, UpgradeError
from persistence import SaveGameError, load_game, save_game
from station import Station


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.station = main.create_station()
        self.station.research = 120
        self.module = self.station.modules[2]
        no_event = patch("station.random.random", return_value=1)
        no_event.start()
        self.addCleanup(no_event.stop)

    def test_outputs_depend_on_level_and_condition(self):
        for module, outputs in (
            (Reactor("Реактор"), (55, 65, 75)),
            (LifeSupport("Жизнеобеспечение"), (20, 25, 30)),
            (Laboratory("Лаборатория"), (8, 12, 16)),
        ):
            for level, expected in enumerate(outputs, start=1):
                with self.subTest(module=type(module).__name__, level=level):
                    module.level = level
                    for condition, output in ((100, expected), (60, expected // 2), (0, 0)):
                        module.condition = condition
                        self.assertEqual(module.operate()[1], output)

    def test_invalid_levels_are_rejected(self):
        for level in (0, 4, -1, True, 2.5, "2", None):
            with self.subTest(level=level), self.assertRaises(ValueError):
                self.module.level = level
        self.assertEqual(self.module.level, 1)

    def test_two_upgrades_charge_research_and_engineer_energy(self):
        self.assertEqual(self.station.upgrade_module(self.module), 40)
        self.assertEqual(self.module.level, 2)
        self.assertEqual(self.module.upgrade_cost, 60)
        self.assertEqual(self.station.upgrade_module(self.module), 60)
        self.assertEqual(self.module.level, 3)
        self.assertEqual(self.module.upgrade_cost, 0)
        self.assertEqual(self.station.research, 20)
        self.assertEqual(self.station.crew[0].energy, 60)
        self.assertEqual(len(self.station.event_log), 2)
        self.assertIn("уровня 3", self.station.event_log[-1])
        self.assertIn("Уровень: 3/3", str(self.module))

    def test_rejected_upgrades_leave_entire_station_unchanged(self):
        scenarios = ("research", "energy", "dead", "missing", "condition", "maximum", "destroyed", "finished")
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                station = main.create_station()
                station.research = 100
                module = station.modules[0]
                if scenario == "research":
                    station.research = 39
                elif scenario == "energy":
                    station.crew[0].energy = 19
                elif scenario == "dead":
                    station.crew[0].health = 0
                elif scenario == "missing":
                    station.crew.pop(0)
                elif scenario == "condition":
                    module.condition = 69
                elif scenario == "maximum":
                    module.level = 3
                elif scenario == "destroyed":
                    station.hull = 0
                else:
                    station.research = 200
                before = station.to_dict()
                with self.assertRaises(UpgradeError):
                    station.upgrade_module(module)
                self.assertEqual(station.to_dict(), before)

    def test_foreign_module_is_not_upgraded(self):
        foreign = Reactor("Чужой реактор")
        before = self.station.to_dict()
        with self.assertRaises(UpgradeError):
            self.station.upgrade_module(foreign)
        self.assertEqual(self.station.to_dict(), before)
        self.assertEqual(foreign.level, 1)

    def test_exact_cost_and_condition_threshold_allow_upgrade(self):
        self.station.research = 40
        self.station.crew[0].energy = 20
        self.module.condition = 70
        self.station.upgrade_module(self.module)
        self.assertEqual((self.station.research, self.station.crew[0].energy), (0, 0))
        self.assertEqual((self.module.level, self.module.condition), (2, 70))

    def test_laboratory_investment_accelerates_research(self):
        station = main.create_station()
        for _ in range(5):
            station.next_day()
        self.assertEqual(station.research, 40)
        station.upgrade_module(station.modules[2])
        self.assertEqual(station.research, 0)
        for _ in range(17):
            station.next_day()
        self.assertTrue(station.mission_completed)
        self.assertEqual((station.day, station.research), (23, 204))

    def test_upgraded_life_support_prevents_oxygen_decline_when_damaged(self):
        life_support = self.station.modules[1]
        self.station.upgrade_module(life_support)
        self.station.upgrade_module(life_support)
        life_support.condition = 60
        self.station.oxygen = 50
        self.station.next_day()
        self.assertEqual(self.station.oxygen, 50)
        self.assertEqual(life_support.energy_cost, 20)

    def test_save_preserves_upgrades_and_next_day_results(self):
        self.station.upgrade_module(self.module)
        self.station.upgrade_module(self.module)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            save_game(self.station, path)
            restored = load_game(path)
        self.assertEqual(restored.to_dict(), self.station.to_dict())
        self.assertIsInstance(restored.modules[2], Laboratory)
        self.assertEqual(restored.modules[2].research_output, 16)
        self.station.next_day()
        restored.next_day()
        self.assertEqual(restored.to_dict(), self.station.to_dict())

    def test_old_saves_default_to_level_one(self):
        data = self.station.to_dict()
        for module in data["modules"]:
            del module["level"]
        restored = Station.from_dict(data)
        self.assertEqual([module.level for module in restored.modules], [1, 1, 1])
        self.assertEqual(restored.modules[2].research_output, 8)

    def test_invalid_saved_level_has_friendly_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            for level in (0, 4, True, None, "2"):
                with self.subTest(level=level):
                    data = self.station.to_dict()
                    data["modules"][0]["level"] = level
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaisesRegex(SaveGameError, "повреждён"):
                        load_game(path)

    def run_menu(self, commands):
        output = io.StringIO()
        with patch("main.create_station", return_value=self.station), patch(
            "builtins.input", side_effect=commands
        ), redirect_stdout(output):
            main.main()
        return output.getvalue()

    def test_menu_upgrade_then_next_day(self):
        output = self.run_menu(["3", "3", "3", "0", "4", "0"])
        self.assertEqual(self.module.level, 2)
        self.assertEqual(self.station.research, 92)
        self.assertIn("улучшен до уровня 2", output)
        self.assertIn("Новая выработка за день: 12", output)

    def test_menu_failure_does_not_stop_game(self):
        self.station.research = 0
        before = self.station.to_dict()
        output = self.run_menu(["3", "3", "3", "0", "0"])
        self.assertIn("Недостаточно исследований", output)
        self.assertIn("Работа симулятора завершена", output)
        self.assertEqual(self.station.to_dict(), before)
