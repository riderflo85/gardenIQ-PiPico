from machine import ADC
from machine import PWM
from machine import Pin as MachinePin

from src.core import FrozenDataclass

AVAILABLE_CHANNELS = ("digit", "pwm", "analog")


class InvalidChannelError(ValueError):
    """Exception raised when an invalid channel type is provided."""

    def __init__(self, channel: str) -> None:
        message = f"Invalid channel type: '{channel}'. Available channels are: {', '.join(AVAILABLE_CHANNELS)}."
        super().__init__(message)


# ------------------------------------------------------------------------------------------------- #
#
# L'utilisation de FrozenDataclass avec __slots__ plutôt qu'un simple dict offre :
# - L'immutabilité : toute tentative de modification lève une AttributeError,
#       garantissant que la whitelist ne peut pas être altérée à l'exécution.
# - L'absence de __dict__ interne sur les instances (grâce aux __slots__),
#      ce qui réduit l'empreinte mémoire — important sur RP2040 (~264 KB de RAM).
# - L'absence des méthodes parasites d'un dict (keys, values, pop, update...),
#       qui ne seraient jamais utilisées ici et consomment de la mémoire inutilement.
class _PinConst(FrozenDataclass):
    __slots__ = ("cls", "IN", "OUT", "PULL_UP", "PULL_DOWN")


class _ADCConst(FrozenDataclass):
    __slots__ = ("cls",)


class _PWMConst(FrozenDataclass):
    __slots__ = ("cls",)


class MpMachine(FrozenDataclass):
    __slots__ = ("Pin", "PWM", "ADC")


# MP_MACHINE expose une whitelist stricte du module `machine` de MicroPython.
# Seules les classes Pin, PWM et ADC sont accessibles, ainsi que les constantes
#   explicitement déclarées (IN, OUT, PULL_UP, PULL_DOWN...).
# Cela empêche qu'une configuration JSON malformée ou malveillante puisse accéder
#   à n'importe quelle classe ou fonction du module machine via getattr(machine, ...).
MP_MACHINE = MpMachine(
    Pin=_PinConst(
        cls=MachinePin,
        IN=MachinePin.IN,
        OUT=MachinePin.OUT,
        PULL_UP=MachinePin.PULL_UP,
        PULL_DOWN=MachinePin.PULL_DOWN,
    ),
    PWM=_PWMConst(cls=PWM),
    ADC=_ADCConst(cls=ADC),
)
# ------------------------------------------------------------------------------------------------- #


class Channel(FrozenDataclass):
    __slots__ = (
        "name",  # str : Channel name
        "pins",  # tuple[int] : Is a tuple of physical Pin numbers
    )


class AllowedPins:
    # Digital
    digits: tuple[Channel, ...] = (
        Channel(name="GP0", pins=(0,)),
        Channel(name="GP1", pins=(1,)),
        Channel(name="GP2", pins=(2,)),
        Channel(name="GP3", pins=(3,)),
        Channel(name="GP4", pins=(4,)),
        Channel(name="GP5", pins=(5,)),
        Channel(name="GP6", pins=(6,)),
        Channel(name="GP7", pins=(7,)),
        Channel(name="GP8", pins=(8,)),
        Channel(name="GP9", pins=(9,)),
        Channel(name="GP10", pins=(10,)),
        Channel(name="GP11", pins=(11,)),
        Channel(name="GP12", pins=(12,)),
        Channel(name="GP13", pins=(13,)),
        Channel(name="GP14", pins=(14,)),
        Channel(name="GP15", pins=(15,)),
        Channel(name="GP16", pins=(16,)),
        Channel(name="GP17", pins=(17,)),
        Channel(name="GP18", pins=(18,)),
        Channel(name="GP19", pins=(19,)),
        Channel(name="GP20", pins=(20,)),
        Channel(name="GP21", pins=(21,)),
        Channel(name="GP22", pins=(22,)),
        Channel(name="GP26", pins=(26,)),
        Channel(name="GP27", pins=(27,)),
        Channel(name="GP28", pins=(28,)),
    )

    # PWM
    pwms: tuple[Channel, ...] = (
        Channel(name="PWM0", pins=(0,)),
        Channel(name="PWM1", pins=(1,)),
        Channel(name="PWM2", pins=(2,)),
        Channel(name="PWM3", pins=(3,)),
        Channel(name="PWM4", pins=(4,)),
        Channel(name="PWM5", pins=(5,)),
        Channel(name="PWM6", pins=(6,)),
        Channel(name="PWM7", pins=(7,)),
        Channel(name="PWM8", pins=(8,)),
        Channel(name="PWM9", pins=(9,)),
        Channel(name="PWM10", pins=(10,)),
        Channel(name="PWM11", pins=(11,)),
        Channel(name="PWM12", pins=(12,)),
        Channel(name="PWM13", pins=(13,)),
        Channel(name="PWM14", pins=(14,)),
        Channel(name="PWM15", pins=(15,)),
        Channel(name="PWM16", pins=(16,)),
        Channel(name="PWM17", pins=(17,)),
        Channel(name="PWM18", pins=(18,)),
        Channel(name="PWM19", pins=(19,)),
        Channel(name="PWM20", pins=(20,)),
        Channel(name="PWM21", pins=(21,)),
        Channel(name="PWM22", pins=(22,)),
        Channel(name="PWM26", pins=(26,)),
        Channel(name="PWM27", pins=(27,)),
        Channel(name="PWM28", pins=(28,)),
    )

    # Analog
    analogs: tuple[Channel, ...] = (
        Channel(name="ADC0", pins=(26,)),
        Channel(name="ADC1", pins=(27,)),
        Channel(name="ADC2", pins=(28,)),
    )

    # I2C
    i2cs: tuple[Channel, ...] = (
        Channel(name="I2C0", pins=(0, 1)),
        Channel(name="I2C1", pins=(2, 3)),
        Channel(name="I2C2", pins=(4, 5)),
        Channel(name="I2C3", pins=(6, 7)),
        Channel(name="I2C4", pins=(8, 9)),
        Channel(name="I2C5", pins=(10, 11)),
        Channel(name="I2C6", pins=(12, 13)),
        Channel(name="I2C7", pins=(14, 15)),
        Channel(name="I2C8", pins=(16, 17)),
        Channel(name="I2C9", pins=(18, 19)),
        Channel(name="I2C10", pins=(20, 21)),
        Channel(name="I2C11", pins=(26, 27)),
    )

    # SPI
    spis: tuple[Channel, ...] = (
        Channel(name="SPI0", pins=(0, 1, 2, 3)),
        Channel(name="SPI1", pins=(4, 5, 6, 7)),
        Channel(name="SPI2", pins=(8, 9, 10, 11)),
        Channel(name="SPI3", pins=(12, 13, 14, 15)),
        Channel(name="SPI4", pins=(16, 17, 18, 19)),
    )

    # UART
    uarts: tuple[Channel, ...] = (
        Channel(name="UART0", pins=(0, 1)),
        Channel(name="UART1", pins=(4, 5)),
        Channel(name="UART2", pins=(8, 9)),
        Channel(name="UART3", pins=(12, 13)),
        Channel(name="UART4", pins=(16, 17)),
    )

    def __init__(self) -> None:
        self.all_pins_number = self._get_all_pins()

    def _get_digit_pins(self) -> set[int]:
        return {p_num for channel in self.digits for p_num in channel.pins}

    def _get_pwm_pins(self) -> set[int]:
        return {p_num for channel in self.pwms for p_num in channel.pins}

    def _get_analog_pins(self) -> set[int]:
        return {p_num for channel in self.analogs for p_num in channel.pins}

    def _get_i2c_pins(self) -> set[int]:
        return {p_num for channel in self.i2cs for p_num in channel.pins}

    def _get_spi_pins(self) -> set[int]:
        return {p_num for channel in self.spis for p_num in channel.pins}

    def _get_uart_pins(self) -> set[int]:
        return {p_num for channel in self.uarts for p_num in channel.pins}

    def _get_all_pins(self) -> set[int]:
        pins_number = set()

        pins_number.update(self._get_digit_pins())
        pins_number.update(self._get_pwm_pins())
        pins_number.update(self._get_analog_pins())
        pins_number.update(self._get_i2c_pins())
        pins_number.update(self._get_spi_pins())
        pins_number.update(self._get_uart_pins())

        return pins_number

    def get_pins_by_channel_type(self, channel_type: str) -> set[int]:
        if channel_type == "digit":
            return self._get_digit_pins()
        elif channel_type == "pwm":
            return self._get_pwm_pins()
        elif channel_type == "analog":
            return self._get_analog_pins()
        elif channel_type == "i2c":
            return self._get_i2c_pins()
        elif channel_type == "spi":
            return self._get_spi_pins()
        elif channel_type == "uart":
            return self._get_uart_pins()
        else:
            raise InvalidChannelError(channel_type)


# singleton
allowed_pins = AllowedPins()
