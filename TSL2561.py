#!/usr/bin/python3
# Library for the TSL2561 Luminosity Sensor

import smbus
import time

class TSL2561:
    """
    This class defines an API for the TSL2561 light sensor chip.

    Example Usage:

    from TSL2561 import TSL2561
    sensor = TSL2561()
    sensor.power_on()
    sensor.get_light_levels()
    sensor.power_off()

    """
    # Command opcode
    _tsl_cmd = 0x80
    # Channel0 sensor data identifier
    _chan0 = 0x0C
    # Channel1 sensor data identifier
    _chan1 = 0x0E

    # Default sensor mode
    default_mode = 'LowShort'

    # Exposure modes
    modes = dict(
        # Normal modes
        LowShort   = 0x00, # x1 Gain 13.7 milliseconds
        LowMed     = 0x01, # x1 Gain 101 milliseconds
        LowLong    = 0x02, # x1 Gain 402 milliseconds
        LowManual  = 0x03, # x1 Gain Manual

        # LowLight Modes
        HighShort  = 0x10, # x16 Gain 13.7 milliseconds
        HighMed    = 0x11, # x16 Gain 100 milliseconds
        HighLong   = 0x12, # x16 Gain 402 milliseconds
        HighManual = 0x13, # x16 Gain Manual
        )

    delays = {'Short': 0.014, 'Med': 0.101, 'Long': 0.403}

    def __init__(self, tsl_addr=0x39):
        # Default I2C address is 0x39, alternate 0x29, 0x49
        self._tsl_addr = tsl_addr

        # Get I2C bus
        self._bus = smbus.SMBus(1)

        # Current mode is not set yet
        self.current_mode = None

    def get_part_no(self):
        part_no_addr = 0x8A
        return self._bus.read_byte_data(self._tsl_addr, part_no_addr)

    def power_on(self):
        # Send power_on (0x03) command
        self._bus.write_byte_data(self._tsl_addr,
                                  0x00 | self._tsl_cmd, 0x03)

    def power_off(self):
        # Send power_off (0x00) command
        self._bus.write_byte_data(self._tsl_addr,
                                  0x00 | self._tsl_cmd, 0x00)

    def set_mode(self, mode=None):
        """
        Set exposure mode.

        mode: mode of exposure (options are one of self.modes.keys())
        """
        if mode is None:
            mode = self.default_mode

        # Resolve mode command
        new_mode = self.modes.get(mode, self.modes[self.default_mode])

        # Update current mode
        if new_mode == self.modes[self.default_mode]:
            self.current_mode = self.default_mode
        else:
            self.current_mode = mode

        # Send mode setting
        self._bus.write_byte_data(self._tsl_addr,
                                  0x01 | self._tsl_cmd, new_mode)

    def get_light_levels(self, wait=True):
        """
        Read block data off of light sensor chip and return measured
        value on both sensors as a tuple of ints
        """
        # Make sure mode is set
        if self.current_mode is None:
            self.set_mode()
            wait = True

        # Wait to read the data off of the chip
        if wait:
            delay = next((v for k, v in self.delays.items()
                          if self.current_mode.endswith(k)))
            time.sleep(delay)

        #Read channel words
        ch0 = self._bus.read_i2c_block_data(self._tsl_addr,
                                            self._chan0 | self._tsl_cmd,
                                            2)
        ch1 = self._bus.read_i2c_block_data(self._tsl_addr,
                                            self._chan1 | self._tsl_cmd,
                                            2)

        # Convert the chanels to base 10 integers
        ch0 = ch0[1] * 256 + ch0[0]
        ch1 = ch1[1] * 256 + ch1[0]

        # Return channel values
        return ch0, ch1


    def manual_exposure(self, delay, gain='Low'):
        """
        Manual exposure method. User defines delay.
        # TODO: set manual mode?

        delay: exposure time in seconds
        """
        # Start manual exposure command
        start_man = 0x1F
        # End manual exposure command
        end_man = 0x1E

        # Start detection
        self._bus.write_byte_data(self._tsl_addr, 0x01 | self._tsl_cmd,
                                  start_man)

        # Sleep for specified delay time- this is the exposure time
        time.sleep(delay)

        # Stop detection
        self._bus.write_byte_data(self._tsl_addr, 0x01 | self._tsl_cmd,
                                  end_man)

    @classmethod
    def luxcalc(Result0, Result1):
        """Basic Lux Calculation value"""
        #see data sheet for lux calculation details
        #and to calculate lux correctly for all modes
        ResDiv = int(Result1)/int(Result0)
        if ResDiv <= 0.52:
            lux = 0.0315 * Result0 - 0.0593 * Result0 * ((ResDiv)**1.4)
        elif ResDiv > 0.52 and ResDiv <= 0.65:
            lux = 0.0229 *Result0 - 0.0291 * Result1
        elif ResDiv > 0.65 and ResDiv <= 0.8:
            lux = 0.0157 * Result0 - 0.0180 * Result1
        elif ResDiv > 0.8 and ResDiv <= 1.3:
            lux = 0.00338 * Result0 - 0.00260 * Result1
        elif ResDiv > 1.3:
            lux = 0
        return lux


