import time

from machine import Pin

# ------- small fake setup to on and off onboard LED -------
led = Pin("LED", Pin.OUT)
led.on()
time.sleep(1.5)
led.off()
# ---------------------------------------------------------
