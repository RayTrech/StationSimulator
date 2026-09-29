from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main
from events import ScientificBreakthroughEvent
from modules import Laboratory, LifeSupport, Reactor
from persistence import SaveGameError, load_game, save_game
from station import Station


class PowerManagementTests(unittest.TestCase):
    def setUp(self):
        self.station = main.create_station()

    def test_switching_is_free_and_logged_without_advancing_day(self):
        module = self.station.modules[2]
        before = self.station.to_dict()
        self.assertTrue(self.station.set_module_enabled(module, False))
        self.assertFalse(module.is_operational)
        self.assertIn("Питание: выключено", str(module))
        self.assertIn("День 1:", self.station.event_log[-1])
        self.assertTrue(self.station.set_module_enabled(module, True))
        self.assertTrue(module.is_operational)
        after = self.station.to_dict()
        after["event_log"] = before["event_log"]
        self.assertEqual(after, before)

    def test_repeating_same_setting_does_not_add_log_entries(self):
        before = self.station.to_dict()
        self.assertFalse(self.station.set_module_enabled(self.station.modules[0], True))
        self.assertEqual(self.station.to_dict(), before)

    def test_disabled_modules_have_zero_output_at_every_condition(self):
        for module in (Reactor("Р"), LifeSupport("Ж"), Laboratory("Л")):
            for condition in (0, 29, 30, 69, 70, 100):
                with self.subTest(module=type(module).__name__, condition=condition):
                    module.condition = condition
                    module.enabled = False
                    self.assertFalse(module.is_operational)
                    self.assertEqual(module.operate()[1], 0)

    def test_disabled_laboratory_preserves_power_for_life_support(self):
        self.station.modules[0].enabled = False
        self.station.modules[2].enabled = False
        self.station.energy = 55
        with patch("station.random.random", return_value=1):
            self.station.next_day()
        self.assertEqual((self.station.energy, self.station.oxygen, self.station.research), (15, 100, 0))
        self.assertIn("отложен", ScientificBreakthroughEvent().apply(self.station))
        self.assertEqual(self.station.research, 0)

    def test_repair_and_upgrade_leave_power_setting_unchanged(self):
        module = self.station.modules[0]
        module.enabled = False
        module.condition = 40
        self.station.crew[0].repair_module(module)
        self.station.research = 40
        self.station.upgrade_module(module)
        self.assertEqual((module.condition, module.level, module.enabled), (70, 2, False))

    def test_invalid_requests_leave_station_and_foreign_module_unchanged(self):
        for scenario in ("foreign", "flag", "victory", "hull", "crew"):
            with self.subTest(scenario=scenario):
                station = main.create_station()
                module, enabled = station.modules[0], False
                if scenario == "foreign":
                    module = Reactor("Чужой реактор")
                elif scenario == "flag":
                    enabled = 0
                elif scenario == "victory":
                    station.research = 200
                elif scenario == "hull":
                    station.hull = 0
                else:
                    for member in station.crew:
                        member.health = 0
                before, module_before = station.to_dict(), module.to_dict()
                with self.assertRaises(ValueError):
                    station.set_module_enabled(module, enabled)
                self.assertEqual(station.to_dict(), before)
                self.assertEqual(module.to_dict(), module_before)

    def test_forecast_matches_real_day_without_using_randomness(self):
        scenarios = (
            ((True, True, True), (100, 100, 100), (1, 1, 1), 100, 100, 0, 100),
            ((True, True, True), (0, 100, 100), (1, 1, 1), 40, 50, 0, 100),
            ((False, False, False), (100, 100, 100), (1, 1, 1), 15, 15, 0, 100),
            ((True, True, True), (60, 60, 60), (3, 3, 3), 10, 20, 0, 100),
            ((True, False, True), (100, 100, 100), (1, 1, 1), 100, 0, 192, 10),
            ((True, True, True), (100, 100, 100), (1, 1, 1), 100, 100, 200, 100),
            ((True, True, True), (100, 100, 100), (1, 1, 1), 100, 100, 0, 0),
        )
        for flags, conditions, levels, energy, oxygen, research, health in scenarios:
            with self.subTest(flags=flags, conditions=conditions, research=research, health=health):
                station = main.create_station()
                for module, flag, condition, level in zip(station.modules, flags, conditions, levels):
                    module.enabled, module.condition, module.level = flag, condition, level
                station.modules.reverse()
                station.energy, station.oxygen, station.research = energy, oxygen, research
                for member in station.crew:
                    member.health = health
                before = station.to_dict()
                with patch("station.random.random") as draw, patch("station.random.choice") as choose:
                    forecast = station.forecast_next_day()
                    draw.assert_not_called()
                    choose.assert_not_called()
                self.assertEqual(station.to_dict(), before)
                with patch("station.random.random", return_value=1):
                    station.next_day()
                self.assertEqual(forecast.to_dict(), station.to_dict())

    def test_forecast_does_not_share_mutable_state_with_current_game(self):
        before = self.station.to_dict()
        forecast = self.station.forecast_next_day()
        forecast.modules[0].enabled = False
        forecast.crew[0].health = 0
        forecast.event_log.append("Прогноз")
        self.assertEqual(self.station.to_dict(), before)

    def test_save_restores_disabled_modules_and_old_save_enables_them(self):
        self.station.modules[2].enabled = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            save_game(self.station, path)
            restored = load_game(path)
        self.assertEqual(restored.to_dict(), self.station.to_dict())
        self.assertEqual(restored.forecast_next_day().research, 0)
        data = self.station.to_dict()
        for module in data["modules"]:
            del module["enabled"]
        self.assertTrue(all(module.enabled for module in Station.from_dict(data).modules))

    def test_invalid_saved_power_setting_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            for enabled in (0, 1, None, "false", [], {}):
                with self.subTest(enabled=enabled):
                    data = self.station.to_dict()
                    data["modules"][0]["enabled"] = enabled
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaisesRegex(SaveGameError, "повреждён"):
                        load_game(path)

    def run_menu(self, commands):
        output = io.StringIO()
        with patch("main.create_station", return_value=self.station), patch(
            "builtins.input", side_effect=commands
        ), patch("station.random.random", return_value=1), redirect_stdout(output):
            main.main()
        return output.getvalue()

    def test_menu_can_disable_forecast_enable_and_advance_day(self):
        output = self.run_menu(["3", "4", "3", "0", "1", "2", "0", "3", "4", "3", "0", "4", "0"])
        self.assertIn("лаборатория» выключен", output)
        self.assertIn("Исследования: 0/200", output)
        self.assertIn("Без случайных событий", output)
        self.assertEqual((self.station.day, self.station.research), (2, 8))
        self.assertEqual(len(self.station.event_log), 2)

    def test_menu_warns_about_suffocation_without_harming_crew(self):
        self.station.oxygen = 15
        output = self.run_menu(["3", "4", "2", "0", "1", "2", "0", "0"])
        self.assertIn("жизненно важная система", output)
        self.assertIn("экипаж потеряет 10 здоровья", output)
        self.assertEqual([member.health for member in self.station.crew], [100, 100])
        self.assertEqual((self.station.day, self.station.oxygen), (1, 15))

    def test_invalid_menu_selection_keeps_game_unchanged(self):
        before = self.station.to_dict()
        for choice in ("текст", "0", "99"):
            with self.subTest(choice=choice):
                self.run_menu(["3", "4", choice, "0", "1", "2", "0", "0"])
                self.assertEqual(self.station.to_dict(), before)
