"""Чтение и запись сохранений без изменения текущей игры при ошибке."""

import json
import os
from pathlib import Path
import tempfile

from station import Station


SAVE_PATH = Path(__file__).with_name("save.json")


class SaveGameError(Exception):
    """Ошибка сохранения или загрузки с сообщением для игрока."""


def save_game(station, path=SAVE_PATH):
    path = Path(path)
    temporary_path = None
    try:
        data = station.to_dict()
        Station.from_dict(data)
        # Замена выполняется только после полной записи: старый файл остаётся
        # целым, если сериализация или запись нового сохранения не удалась.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(data, file, indent=4, ensure_ascii=False, allow_nan=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    except (OSError, ValueError) as error:
        raise SaveGameError("Не удалось сохранить игру. Проверьте доступ к файлу.") from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def load_game(path=SAVE_PATH):
    try:
        with Path(path).open(encoding="utf-8-sig") as file:
            data = json.load(file)
        return Station.from_dict(data)
    except FileNotFoundError as error:
        raise SaveGameError("Файл сохранения не найден.") from error
    except (ValueError, RecursionError) as error:
        raise SaveGameError("Файл сохранения повреждён или имеет неверный формат.") from error
    except OSError as error:
        raise SaveGameError("Не удалось прочитать сохранение. Проверьте доступ к файлу.") from error
