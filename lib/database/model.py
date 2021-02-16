from enum import Enum


class TemperatureUnit(Enum):
    Celsius = 1
    Fahrenheit = 2

    def to_str(self) -> str:
        if self == TemperatureUnit.Celsius:
            return "Celsius"
        else:
            return "Fahrenheit"


class UserSettings:
    def __init__(self, owner: int, temp_unit: TemperatureUnit):
        self.temp_unit = temp_unit
        self.owner = owner
