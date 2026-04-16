# import time

# from machine import Pin

# # ------- small fake setup to on and off onboard LED -------
# led = Pin("LED", Pin.OUT)
# led.on()
# time.sleep(1.5)
# led.off()
# # ---------------------------------------------------------


# POUR TEST À LA MAIN !!
from src.protocols import usb

# Setup block
usb.setup()

# Main process block
usb.process()


while True:
    pass
