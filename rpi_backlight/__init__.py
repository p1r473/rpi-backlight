import time
from os import PathLike
from pathlib import Path
from typing import Any, Callable, Union

__author__ = "Linus Groh"
__version__ = "2.0.0a1"
__all__ = ["Backlight"]

BACKLIGHT_SYSFS_PATH = "/sys/class/backlight/rpi_backlight/"


def _permission_denied() -> None:
    raise PermissionError(
        "You must either run this program as root or change the permissions "
        "for the backlight access as described on the GitHub page."
    )


class Backlight:
    def __init__(
        self, backlight_sysfs_path: Union[str, bytes, PathLike] = BACKLIGHT_SYSFS_PATH
    ):
        self._backlight_sysfs_path = Path(backlight_sysfs_path)
        self._max_brightness = self._get_value("max_brightness")  # 255
        self._fade_duration = 0

    def _get_value(self, name: str) -> int:
        try:
            return int((self._backlight_sysfs_path / name).read_text())
        except (OSError, IOError) as e:
            if e.errno == 13:
                _permission_denied()
            raise e

    def _set_value(self, name: str, value: int) -> None:
        try:
            (self._backlight_sysfs_path / name).write_text(str(value))
        except (OSError, IOError) as e:
            if e.errno == 13:
                _permission_denied()
            raise e

    def _normalize_brightness(self, value: int) -> int:
        return int(round(value / self._max_brightness * 100))

    def _denormalize_brightness(self, value: int) -> int:
        return int(round(value * self._max_brightness / 100))

    @property
    def brightness(self) -> float:
        """Return the display brightness."""
        return self._normalize_brightness(self._get_value("actual_brightness"))

    @brightness.setter
    def brightness(self, value: float) -> None:
        """Set the display brightness."""
        # isinstance(True, int) is True, so additional check for bool.
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("value must be a number, got {0}".format(type(value)))
        if value < 0 or value > 100:
            raise ValueError("value must be in range 0-100, got {0}")

        if self._fade_duration > 0:
            current_value = self.brightness
            diff = abs(value - current_value)
            while current_value != value:
                current_value += 1 if current_value < value else -1
                self._set_value("brightness", self._denormalize_brightness(value))
                time.sleep(self._fade_duration / diff)
        else:
            self._set_value("brightness", self._denormalize_brightness(value))

    @property
    def power(self) -> bool:
        """Return whether the display is powered on or off."""
        # 0 is on, 1 is off
        return not self._get_value("bl_power")

    @power.setter
    def power(self, on: bool) -> bool:
        """Set the display power on or off."""
        if not isinstance(on, bool):
            raise TypeError("value must be a bool, got {0}".format(type(on)))
        # 0 is on, 1 is off
        self._set_value("bl_power", int(not on))