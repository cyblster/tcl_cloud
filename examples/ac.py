# Пример управления кондиционером TCL

from aenum import Enum, NoAlias

from tcl_cloud import TclCloud


class Mode(Enum):
    auto = 0
    cool = 1
    dry = 2
    fan_only = 3
    heat = 4


class FanSpeed(Enum, settings=NoAlias):
    auto = 0
    quiet = 2
    low = 2
    medium = 4
    high = 6
    turbo = 6


class TclAC:
    def __init__(self, cloud: TclCloud):
        self.__cloud = cloud

        self.device_id = 'CB0AzBFAAAE'

    def set_power(self, power: bool) -> bool:
        return self.__cloud.send_action(self.device_id, powerSwitch=int(power))

    def set_mode(self, mode: Mode) -> bool:
        return self.__cloud.send_action(self.device_id, workMode=mode.value)

    def set_temperature(self, temperature: int) -> bool:
        if not 16 <= temperature <= 31:
            raise ValueError(f'Temperature must be between 16 and 31')

        return self.__cloud.send_action(self.device_id, targetTemperature=temperature)

    def set_fan_speed(self, fan_speed: FanSpeed) -> bool:
        silence_switch = 1 if fan_speed == FanSpeed.quiet else 0
        turbo = 1 if fan_speed == FanSpeed.turbo else 0

        return self.__cloud.send_action(self.device_id, windSpeed=fan_speed.value,
                                        silenceSwitch=silence_switch, turbo=turbo)

    @property
    def state(self) -> dict:
        return self.__cloud.get_info(self.device_id)['state']

    @property
    def power(self) -> bool:
        return bool(self.state['desired']['powerSwitch'])

    @property
    def mode(self) -> Mode:
        return Mode(self.state['desired']['workMode']).name

    @property
    def target_temperature(self) -> int:
        return self.state['desired']['targetTemperature']

    @property
    def current_temperature(self) -> int:
        return self.state['desired']['currentTemperature']

    @property
    def fan_speed(self) -> FanSpeed:
        state = self.state

        fan_speed = 'auto'
        if state['desired']['silenceSwitch']:
            fan_speed = 'quiet'
        elif state['desired']['turbo']:
            fan_speed = 'turbo'
        elif state['desired']['windSpeed'] == 2:
            fan_speed = 'low'
        elif state['desired']['windSpeed'] == 4:
            fan_speed = 'medium'
        elif state['desired']['windSpeed'] == 6:
            fan_speed = 'high'

        return FanSpeed[fan_speed].name


if __name__ == '__main__':
    username = 'foo'
    password = 'bar'

    tcl_cloud = TclCloud(username, password, region='ru')
    ac = TclAC(tcl_cloud)

    # print(ac.state)
