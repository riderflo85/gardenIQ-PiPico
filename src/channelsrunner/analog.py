from machine import ADC

__all__ = ("run_get",)


def run_get(executor: ADC) -> int:
    return executor.read_u16()
