from shush.board import Board
from shush.drivers import tmc5160_reg as reg
from gpiozero import DigitalOutputDevice
from shush.params import Ramp as ramp
import time
import shush.boards.planktoscope_hat_v1 as s1


class Motor(Board):
    def __init__(self, motor: int):
        super().__init__()

        # Build pin names dynamically
        cs_attr = f"m{motor}_cs"
        en_attr = f"m{motor}_enable"

        # Check if pins exist
        if not hasattr(s1, cs_attr) or not hasattr(s1, en_attr):
            raise ValueError(f"Motor {motor} is not supported by this board configuration.")

        # Set up CS and Enable pins as DigitalOutputDevice
        self.chip_select = DigitalOutputDevice(getattr(s1, cs_attr), initial_value=True)
        self.enable = DigitalOutputDevice(getattr(s1, en_attr), initial_value=True)

        self.motor = motor
        self.default_settings()

    def enable_motor(self):
        self.enable.off()  # LOW to enable

    def disable_motor(self):
        self.enable.on()   # HIGH to disable

    def send_data(self, data_array: list) -> int:
        self.chip_select.off()
        response = Board.spi.xfer2(data_array)
        self.chip_select.on()
        return response

    def default_settings(self):
        self.write(reg.GCONF, 0x0000000C)
        self.write(reg.CHOPCONF, 0x000100C3)
        self.write(reg.IHOLD_IRUN, 0x00080501)
        self.write(reg.TPOWERDOWN, 0x0000000A)
        self.write(reg.TPWMTHRS, 0x000001F4)

        self.reset_ramp_defaults()

        self.write(reg.RAMPMODE, 0)
        self.write(reg.XACTUAL, 0)
        self.write(reg.XTARGET, 0)

    def set_VSTART(self, value: int): self.write(reg.VSTART, value); ramp.VSTART = value
    def set_A1(self, value: int): self.write(reg.A1, value); ramp.A1 = value
    def set_V1(self, value: int): self.write(reg.V1, value); ramp.V1 = value
    def set_AMAX(self, value: int): self.write(reg.AMAX, value); ramp.AMAX = value
    def set_VMAX(self, value: int): self.write(reg.VMAX, value); ramp.VMAX = value
    def set_DMAX(self, value: int): self.write(reg.DMAX, value); ramp.DMAX = value
    def set_D1(self, value: int): self.write(reg.D1, value); ramp.D1 = value
    def set_VSTOP(self, value: int): self.write(reg.VSTOP, value); ramp.VSTOP = value

    def write_ramp_params(self):
        self.set_VSTART(ramp.VSTART)
        self.set_A1(ramp.A1)
        self.set_V1(ramp.V1)
        self.set_AMAX(ramp.AMAX)
        self.set_VMAX(ramp.VMAX)
        self.set_DMAX(ramp.DMAX)
        self.set_D1(ramp.D1)
        self.set_VSTOP(ramp.VSTOP)

    def reset_ramp_defaults(self):
        ramp.VSTART = 1
        ramp.A1 = 25000
        ramp.V1 = 250000
        ramp.AMAX = 5000
        ramp.VMAX = 1000000
        ramp.DMAX = 5000
        ramp.D1 = 50000
        ramp.VSTOP = 10
        self.write_ramp_params()

    def enable_switch(self, direction: int):
        setting_array = [0] * 12
        setting_array[0] = 1

        if direction == 1:
            setting_array[6] = 1
            setting_array[11] = 1
            error = False
        elif direction == 2:
            setting_array[4] = 1
            setting_array[10] = 1
            error = False
        else:
            print("Invalid input! Use 1 (left), or 2 (right).")
            error = True

        if not error:
            switch_settings = int(''.join(str(i) for i in setting_array), 2)
            self.write(reg.SWMODE, switch_settings)

    def get_position(self) -> int:
        return self.twos_comp(self.read(reg.XACTUAL))

    def get_latched_position(self) -> int:
        return self.twos_comp(self.read(reg.XLATCH))

    def get_velocity(self) -> int:
        return self.twos_comp(self.read(reg.VACTUAL), 24)

    def go_to(self, position: int):
        self.position_mode()
        self.write_ramp_params()

        min_pos = -(2**31)
        max_pos = (2**31) - 1

        if position > max_pos:
            position = max_pos
            print("Clipped to maximum position.")
        elif position < min_pos:
            position = min_pos
            print("Clipped to minimum position.")

        self.write(reg.XTARGET, position)

    def calibrate_home(self, direction: int):
        self.enable_switch(direction)
        self.get_ramp_status()

        if direction == 1:
            switch_pressed = int(self.get_ramp_status.status_stop_l)
            if switch_pressed == 1:
                self.go_to(512000)
                while int(self.get_ramp_status.status_stop_l) == 1:
                    self.get_ramp_status()
        elif direction == 2:
            switch_pressed = int(self.get_ramp_status.status_stop_r)
            if switch_pressed == 1:
                self.go_to(-512000)
                while int(self.get_ramp_status.status_stop_r) == 1:
                    self.get_ramp_status()
        else:
            print("Invalid direction")
            return

        self.go_to(-2560000)
        time.sleep(0.1)
        while self.get_velocity() != 0:
            self.get_velocity()

        self.hold_mode()
        diff = self.get_position() - self.get_latched_position()
        self.write(reg.XACTUAL, diff)
        self.write(reg.RAMPSTAT, 4)
        self.go_to(0)
        print("Homing complete!")

    def move_velocity(self, dir: int, v_max: int = None, a_max: int = None):
        if v_max is not None: self.write(reg.VMAX, v_max)
        if a_max is not None: self.write(reg.AMAX, a_max)

        if dir == 0: mode = 1
        elif dir == 1: mode = 2
        else:
            print("Invalid dir. Use 0 (left) or 1 (right).")
            return

        self.write(reg.RAMPMODE, mode)

    def stop_motor(self):
        self.move_velocity(0, v_max=0)
        while self.get_velocity() != 0:
            time.sleep(0.01)
        self.hold_mode()
        self.set_VMAX(ramp.VMAX)

    def hold_mode(self): self.write(reg.RAMPMODE, 3)
    def position_mode(self): self.write(reg.RAMPMODE, 0)

    def get_ramp_status(self):
        val = self.read(reg.RAMPSTAT)
        bits = list("{0:014b}".format(val))

        Motor.get_ramp_status.status_sg = bits[0]
        Motor.get_ramp_status.second_move = bits[1]
        Motor.get_ramp_status.t_zerowait_active = bits[2]
        Motor.get_ramp_status.vzero = bits[3]
        Motor.get_ramp_status.position_reached = bits[4]
        Motor.get_ramp_status.velocity_reached = bits[5]
        Motor.get_ramp_status.event_pos_reached = bits[6]
        Motor.get_ramp_status.event_stop_sg = bits[7]
        Motor.get_ramp_status.event_stop_r = bits[8]
        Motor.get_ramp_status.event_stop_l = bits[9]
        Motor.get_ramp_status.status_latch_r = bits[10]
        Motor.get_ramp_status.status_latch_l = bits[11]
        Motor.get_ramp_status.status_stop_r = bits[12]
        Motor.get_ramp_status.status_stop_l = bits[13]

    def read(self, address: int) -> int:
        buffer = [0] * 5
        buffer[0] = address & 0x7F
        self.send_data(buffer)
        response = self.send_data(buffer)
        return ((response[1] << 24) |
                (response[2] << 16) |
                (response[3] << 8) |
                response[4])

    def write(self, address: int, data: int) -> int:
        buffer = [address | 0x80,
                  (data >> 24) & 0xFF,
                  (data >> 16) & 0xFF,
                  (data >> 8) & 0xFF,
                  data & 0xFF]
        return self.send_data(buffer)

    def twos_comp(self, value: int, bits: int = 32) -> int:
        return value - (1 << bits) if (value & (1 << (bits - 1))) else value
