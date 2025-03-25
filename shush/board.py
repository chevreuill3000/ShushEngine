import shush.boards.planktoscope_hat_v1 as s1
import spidev
from gpiozero import DigitalOutputDevice


class Board:

    def __init__(self):
        # Initialize the peripherals (SPI and GPIO)
        self.init_spi()
        self.init_gpio_state()

    def init_gpio_state(self):
        # Initialize CS pins
        self.cs_pins = {
            'm0': DigitalOutputDevice(s1.m0_cs, initial_value=True),
            'm1': DigitalOutputDevice(s1.m1_cs, initial_value=True)
        }

        # Initialize Enable pins
        self.enable_pins = {
            'm0': DigitalOutputDevice(s1.m0_enable, initial_value=False),
            'm1': DigitalOutputDevice(s1.m1_enable, initial_value=False)
        }

    def init_spi(self):
        # Initialize SPI Bus for motor drivers.
        Board.spi = spidev.SpiDev()

        # Open(Bus, Device)
        Board.spi.open(0, 0)

        # 1 MHZ
        Board.spi.max_speed_hz = 1000000

        # 8 bits per word (32-bit word is broken into 4x 8-bit words)
        Board.spi.bits_per_word = 8

        Board.spi.loop = False

        # SPI Mode 3
        Board.spi.mode = 3

    def deinitBoard(self):
        # Close the board and release peripherals.
        for pin in self.cs_pins.values():
            pin.close()
        for pin in self.enable_pins.values():
            pin.close()
        Board.spi.close()
