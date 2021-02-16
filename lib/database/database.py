import abc
import typing
from .model import UserSettings, TemperatureUnit

class SettingsDao:
    @abc.abstractmethod
    def update_settings(self, settings: UserSettings):
        pass
    
    @abc.abstractmethod
    def fetch_settings(self, user_id: int) -> typing.Optional[UserSettings]:
        pass

    def fetch_settings_or_default(self, user_id: int) -> UserSettings:
        settings = self.fetch_settings(user_id)
        if settings is None:
            return UserSettings(user_id,
                                TemperatureUnit.Celsius)
        return settings
    

class Database:
    @abc.abstractmethod
    def settings_dao() -> SettingsDao:
        pass
