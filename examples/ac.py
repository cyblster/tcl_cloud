# Пример управления кондиционером TCL

from enum import Enum

from tcl_cloud import TclCloud


class Mode(Enum):
    auto = 0
    cool = 1
    dry = 2
    fan_only = 3
    heat = 4


class FanSpeed(Enum):  # (windSpeed, silenceSwitch, turbo)
    auto = (0, 0, 0)
    quiet = (2, 1, 0)
    low = (2, 0, 0)
    medium = (4, 0, 0)
    high = (6, 0, 0)
    turbo = (6, 0, 1)


class TclAC:
    def __init__(self, cloud: TclCloud):
        self.__cloud = cloud

        self.device_id = 'CB0AzBFAAAE'

    def set_power(self, power: bool) -> bool:
        data = {
            'powerSwitch': int(power)
        }
        return self.__cloud.send_action(self.device_id, **data)

    def set_mode(self, mode: Mode) -> bool:
        data = {
            'workMode': mode.value
        }

        return self.__cloud.send_action(self.device_id, **data)

    def set_temperature(self, temperature: int) -> bool:
        if not 16 <= temperature <= 31:
            raise ValueError(f'Temperature must be between 16 and 31')

        data = {
            'targetTemperature': temperature
        }

        return self.__cloud.send_action(self.device_id, **data)

    def set_fan_speed(self, fan_speed: FanSpeed) -> bool:
        wind_speed, silence_switch, turbo = fan_speed.value

        data = {
            'windSpeed': wind_speed,
            'silenceSwitch': silence_switch,
            'turbo': turbo
        }

        return self.__cloud.send_action(self.device_id, **data)

    @property
    def state(self) -> dict:
        return self.__cloud.get_info(self.device_id)['state']['desired']

    @property
    def power(self) -> bool:
        return bool(self.state['powerSwitch'])

    @property
    def mode(self) -> Mode:
        return Mode(self.state['workMode'])

    @property
    def target_temperature(self) -> int:
        return self.state['targetTemperature']

    @property
    def current_temperature(self) -> int:
        return self.state['currentTemperature']

    @property
    def fan_speed(self) -> FanSpeed:
        state = self.state

        return FanSpeed((state['windSpeed'], state['silenceSwitch'], state['turbo']))


if __name__ == '__main__':
    username = '########'
    password = '########'

    tcl_cloud = TclCloud(username, password, region='ru')
    ac = TclAC(tcl_cloud)

    print(ac.state)
