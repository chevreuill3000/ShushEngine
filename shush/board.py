import shush.boards.planktoscope_hat_v1 as s1
import spidev
from gpiozero import DigitalOutputDevice
from gpiozero.exc import GPIOPinInUse

class Board:
    _gpio_initialized = False  # Flag de classe
    cs_pins = {}               # Pins CS partagés entre moteurs
    enable_pins = {}           # Pins ENABLE partagés entre moteurs

    def __init__(self):
        self.init_spi()

        if not Board._gpio_initialized:
            self.init_gpio_state()
            Board._gpio_initialized = True
        else:
            print("⚠️ GPIO already initialized, skipping duplicate setup.")

    def init_gpio_state(self):
        # Initialize CS pins
        for label, pin in {
            'm0': s1.m0_cs,
            'm1': s1.m1_cs
        }.items():
            try:
                Board.cs_pins[label] = DigitalOutputDevice(pin, initial_value=True)
            except GPIOPinInUse:
                print(f"⚠️ CS pin GPIO{pin} already in use. Skipping '{label}'.")

        # Initialize Enable pins
        for label, pin in {
            'm0': s1.m0_enable,
            'm1': s1.m1_enable
        }.items():
            try:
                Board.enable_pins[label] = DigitalOutputDevice(pin, initial_value=False)
            except GPIOPinInUse:
                print(f"⚠️ Enable pin GPIO{pin} already in use. Skipping '{label}'.")

    def init_spi(self):
        # Initialize SPI Bus for motor drivers.
        Board.spi = spidev.SpiDev()
        Board.spi.open(0, 0)
        Board.spi.max_speed_hz = 1000000
        Board.spi.bits_per_word = 8
        Board.spi.loop = False
        Board.spi.mode = 3

    def deinitBoard(self):
        # Close the board and release peripherals.
        for pin in Board.cs_pins.values():
            pin.close()
        for pin in Board.enable_pins.values():
            pin.close()
        Board.spi.close()
