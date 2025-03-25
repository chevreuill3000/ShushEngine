import shush.boards.planktoscope_hat_v1 as s1
import spidev
from gpiozero import DigitalOutputDevice
from gpiozero.exc import GPIOPinInUse


class Board:
    _gpio_initialized = False  # Classe-level flag

    def __init__(self):
        self.cs_pins = {}
        self.enable_pins = {}

        self.init_spi()

        if not Board._gpio_initialized:
            self.init_gpio_state()
            Board._gpio_initialized = True
        else:
            print("⚠️ GPIO already initialized, skipping duplicate setup.")

    def init_gpio_state(self):
        # Try to initialize CS pins
        for label, pin in {
            'm0': s1.m0_cs,
            'm1': s1.m1_cs
        }.items():
            try:
                self.cs_pins[label] = DigitalOutputDevice(pin, initial_value=True)
            except GPIOPinInUse:
                print(f"⚠️ CS pin GPIO{pin} already in use. Skipping '{label}'.")

        # Try to initialize Enable pins
        for label, pin in {
            'm0': s1.m0_enable,
            'm1': s1.m1_enable
        }.items():
            try:
                self.enable_pins[label] = DigitalOutputDevice(pin, initial_value=False)
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
        for pin in self.cs_pins.values():
            pin.close()
        for pin in self.enable_pins.values():
            pin.close()
        Board.spi.close()
