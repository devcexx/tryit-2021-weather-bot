import typing
from .database import Database, SettingsDao
from .model import UserSettings, TemperatureUnit


class DynamoDatabase(Database):
    def __init__(self, table):
        self.table = table
        self._settings_dao = DynamoSettingsDao(self)

    def settings_dao(self):
        return self._settings_dao


class DynamoSettingsDao(SettingsDao):
    def __init__(self, database: DynamoDatabase):
        self.database = database
        self.table = self.database.table

    def temp_unit_to_ddb(unit: TemperatureUnit) -> str:
        if unit == TemperatureUnit.Celsius:
            return "C"
        else:
            return "F"

    def temp_unit_from_ddb(unit: str) -> TemperatureUnit:
        if unit == "C":
            return TemperatureUnit.Celsius
        elif unit == "F":
            return TemperatureUnit.Fahrenheit
        else:
            raise Exception(f"Unrecognized temp unit: {unit}")

    def update_settings(self, settings: UserSettings):
        table = self.database.table
        table.put_item(Item={
            'key': f"u{settings.owner}",
            'scope': 'settings',
            'temp_unit': DynamoSettingsDao.temp_unit_to_ddb(settings.temp_unit)
        })

    def fetch_settings(self, user_id: int) -> typing.Optional[UserSettings]:
        response = self.table.get_item(
            Key={
                'key': f"u{user_id}",
                'scope': 'settings'
            }
        )
        item = response.get("Item")
        if item is None:
            return None

        temp_unit = item.get("temp_unit")
        if temp_unit is not None:
            temp_unit = DynamoSettingsDao.temp_unit_from_ddb(temp_unit)

        return UserSettings(user_id, temp_unit)
