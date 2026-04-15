from src.core import FrozenDataclass
from src.core.enum import PseudoEnum


class BusType(PseudoEnum):
    DIGIT = "digit"
    PWM = "pwm"
    ANALOG = "analog"
    I2C = "i2c"
    SPI = "spi"
    UART = "uart"

    @classmethod
    def check_value(cls, value: str) -> str:
        if value in cls.values():
            return value
        raise ValueError(f"Invalid BusType value: {value}. Expected one of: {', '.join(cls.values())}")


class Bus(FrozenDataclass):
    __slots__ = (
        "name",  # str : Bus name
        "pins",  # tuple[int] : Is a tuple of physical Pin numbers
    )


class AllowedPins:
    # Digital
    digits: tuple[Bus, ...] = (
        Bus(name="GP0", pins=(0,)),
        Bus(name="GP1", pins=(1,)),
        Bus(name="GP2", pins=(2,)),
        Bus(name="GP3", pins=(3,)),
        Bus(name="GP4", pins=(4,)),
        Bus(name="GP5", pins=(5,)),
        Bus(name="GP6", pins=(6,)),
        Bus(name="GP7", pins=(7,)),
        Bus(name="GP8", pins=(8,)),
        Bus(name="GP9", pins=(9,)),
        Bus(name="GP10", pins=(10,)),
        Bus(name="GP11", pins=(11,)),
        Bus(name="GP12", pins=(12,)),
        Bus(name="GP13", pins=(13,)),
        Bus(name="GP14", pins=(14,)),
        Bus(name="GP15", pins=(15,)),
        Bus(name="GP16", pins=(16,)),
        Bus(name="GP17", pins=(17,)),
        Bus(name="GP18", pins=(18,)),
        Bus(name="GP19", pins=(19,)),
        Bus(name="GP20", pins=(20,)),
        Bus(name="GP21", pins=(21,)),
        Bus(name="GP22", pins=(22,)),
        Bus(name="GP26", pins=(26,)),
        Bus(name="GP27", pins=(27,)),
        Bus(name="GP28", pins=(28,)),
    )

    # PWM
    pwms: tuple[Bus, ...] = (
        Bus(name="PWM0", pins=(0,)),
        Bus(name="PWM1", pins=(1,)),
        Bus(name="PWM2", pins=(2,)),
        Bus(name="PWM3", pins=(3,)),
        Bus(name="PWM4", pins=(4,)),
        Bus(name="PWM5", pins=(5,)),
        Bus(name="PWM6", pins=(6,)),
        Bus(name="PWM7", pins=(7,)),
        Bus(name="PWM8", pins=(8,)),
        Bus(name="PWM9", pins=(9,)),
        Bus(name="PWM10", pins=(10,)),
        Bus(name="PWM11", pins=(11,)),
        Bus(name="PWM12", pins=(12,)),
        Bus(name="PWM13", pins=(13,)),
        Bus(name="PWM14", pins=(14,)),
        Bus(name="PWM15", pins=(15,)),
        Bus(name="PWM16", pins=(16,)),
        Bus(name="PWM17", pins=(17,)),
        Bus(name="PWM18", pins=(18,)),
        Bus(name="PWM19", pins=(19,)),
        Bus(name="PWM20", pins=(20,)),
        Bus(name="PWM21", pins=(21,)),
        Bus(name="PWM22", pins=(22,)),
        Bus(name="PWM26", pins=(26,)),
        Bus(name="PWM27", pins=(27,)),
        Bus(name="PWM28", pins=(28,)),
    )

    # Analog
    analogs: tuple[Bus, ...] = (
        Bus(name="ADC0", pins=(26,)),
        Bus(name="ADC1", pins=(27,)),
        Bus(name="ADC2", pins=(28,)),
    )

    # I2C
    i2cs: tuple[Bus, ...] = (
        Bus(name="I2C0", pins=(0, 1)),
        Bus(name="I2C1", pins=(2, 3)),
        Bus(name="I2C2", pins=(4, 5)),
        Bus(name="I2C3", pins=(6, 7)),
        Bus(name="I2C4", pins=(8, 9)),
        Bus(name="I2C5", pins=(10, 11)),
        Bus(name="I2C6", pins=(12, 13)),
        Bus(name="I2C7", pins=(14, 15)),
        Bus(name="I2C8", pins=(16, 17)),
        Bus(name="I2C9", pins=(18, 19)),
        Bus(name="I2C10", pins=(20, 21)),
        Bus(name="I2C11", pins=(26, 27)),
    )

    # SPI
    spis: tuple[Bus, ...] = (
        Bus(name="SPI0", pins=(0, 1, 2, 3)),
        Bus(name="SPI1", pins=(4, 5, 6, 7)),
        Bus(name="SPI2", pins=(8, 9, 10, 11)),
        Bus(name="SPI3", pins=(12, 13, 14, 15)),
        Bus(name="SPI4", pins=(16, 17, 18, 19)),
    )

    # UART
    uarts: tuple[Bus, ...] = (
        Bus(name="UART0", pins=(0, 1)),
        Bus(name="UART1", pins=(4, 5)),
        Bus(name="UART2", pins=(8, 9)),
        Bus(name="UART3", pins=(12, 13)),
        Bus(name="UART4", pins=(16, 17)),
    )

    def __init__(self) -> None:
        self.all_pins_number = self._get_all_pins()

    def _get_all_pins(self) -> set[int]:
        pins_number = set()

        for p_digit in self.digits:
            pins_number.update({p_num for p_num in p_digit.pins})

        for p_pwm in self.pwms:
            pins_number.update({p_num for p_num in p_pwm.pins})

        for p_adc in self.analogs:
            pins_number.update({p_num for p_num in p_adc.pins})

        for p_i2c in self.i2cs:
            pins_number.update({p_num for p_num in p_i2c.pins})

        for p_spi in self.spis:
            pins_number.update({p_num for p_num in p_spi.pins})

        for p_uart in self.uarts:
            pins_number.update({p_num for p_num in p_uart.pins})

        return pins_number


# singleton
allowed_pins = AllowedPins()
