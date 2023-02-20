import unittest
import keller_protocol


class TestKellerProtocol(unittest.TestCase):
    def setUp(self):
        """
        Will be called for every single test
        Tests have to be done with an X-Line Transmitter
        Adjust the Serial Settings
        """
        self.bus = keller_protocol.KellerProtocol(
            "COM17", baud_rate=115200, timeout=200 / 1000, echo=True
        )
        self.address = 2
        # init device
        self.bus.f48(self.address)

    def test_crc16(self):
        self.assertEqual(
            self.bus._crc16([2, 48], 2), b"\xc4\x00", "Should be xc4 and x00"
        )

    def test_f30_31_set_gain_factor(self):
        pressure_gain = self.bus.f30(self.address, 65)
        print(f"Test F30: Read Gain factor of pressure sensor:{pressure_gain:.3f}")
        new_gain_factor = 2.1
        print(f"Test F31: Set Gain factor or pressure sensor to {new_gain_factor:.1f}")
        self.bus.f31(self.address, 65, new_gain_factor)
        gain_factor = self.bus.f30(self.address, 65)
        self.assertAlmostEqual(
            first=gain_factor,
            second=new_gain_factor,
            places=2,
            msg=f"Should be {new_gain_factor:.1f}",
        )
        gain_factor = round(gain_factor, 1)
        self.assertEqual(
            gain_factor, new_gain_factor, f"Should be {new_gain_factor:.1f}"
        )
        print(
            f"Test F31: Set Gain factor of pressure sensor back to {pressure_gain:.3f}"
        )
        self.bus.f31(self.address, 65, pressure_gain)

    def test_f32_read_temp_int(self):
        temp_interval = self.bus.f32(self.address, 3)
        print(
            f"Test F32: Read Configuration nr.:3 temperature measurement interval in seconds:{temp_interval}"
        )
        self.assertEqual(
            1, temp_interval, "temperature measurement interval should be 1"
        )

    def test_f48(self):
        firmware = self.bus.f48(self.address)
        print(f"Firmware Version: {firmware}")
        self.assertIsNotNone(firmware, "Should return Firmware string and not None")

    def test_f66_set_read_address(self):
        new_address = 101
        print(f"Test F66: Set address to {new_address}")
        self.bus.f66(self.address, new_address)
        self.assertEqual(
            self.bus.f66(250, 0), 101, f"New address should be {new_address}"
        )
        print(f"Test F66: Read address: {self.bus.f66(250, 0)}")
        print(f"Test F66: Set address back to {self.address}")
        self.bus.f66(new_address, self.address)

    def test_f69_read_serial(self):
        print(f"Test F69: Read Serial Number")
        serial_number = self.bus.f69(self.address)
        print(f"Serial number:{serial_number}")
        self.assertIsNotNone(
            serial_number, "Should return Serialnumber string and not None"
        )

    def test_f73_read_tob1(self):
        temperature = self.bus.f73(self.address, 4)
        print(f"Test F73: Read value of channel 4 (TOB1): {temperature:.3f}")
        # Temperature should "normally" be in between low_temp and high_temp
        low_temp = 15
        high_temp = 30
        self.assertGreater(
            temperature,
            low_temp,
            f"Temperature is below {low_temp:.1f}°C. Check if value is valid: {temperature}",
        )
        self.assertLess(
            temperature,
            high_temp,
            f"Temperature is above {high_temp:.1f}°C. Check if value is valid: {temperature}",
        )

    def test_f74_read_tob1(self):
        temperature = self.bus.f74(self.address, 4)
        print(f"Test F74: Read value of channel 4 (TOB1): {temperature}")
        # Temperature should "normally" be in range 15 - 30°C
        low_temp = 1500
        high_temp = 3000
        self.assertGreater(
            temperature,
            low_temp,
            f"Temperature is below {low_temp / 100 :.1f}°C. Check if value is valid: {temperature / 100}",
        )
        self.assertLess(
            temperature,
            high_temp,
            f"Temperature is above {high_temp / 100 :.1f}°C. Check if value is valid: {temperature / 100}",
        )

    def test_f95_set_zero_p1(self):
        print(f"Set zero point of P1")
        self.bus.f95(self.address, cmd=0)
        p1 = self.bus.f73(self.address, 1)
        print(f"Test F95: Read value of channel 1 (P1): {p1}")
        p_max = 0.001
        p_min = -0.001
        self.assertGreater(
            p1, p_min, f"p1 is below {p_min:.3f}bar. Check if value is valid: {p1}"
        )
        self.assertLess(
            p1, p_max, f"p1 is above {p_max:.3f}bar. Check if value is valid: {p1}"
        )
        print(f"Set zero point back to standard value of P1")
        self.bus.f95(self.address, cmd=1)

    def test_f95_set_to_value_p1(self):
        target_pressure = 2.5
        print(f"Set zero point of P1 to {target_pressure} bar")
        self.bus.f95(self.address, cmd=0, value=target_pressure)
        p1 = self.bus.f73(self.address, 1)
        print(f"Test F95: Read value of channel 1 (P1): {p1}")
        threshold = 0.001
        self.assertGreater(
            p1,
            target_pressure - threshold,
            f"p1 is below {target_pressure - threshold:.3f}bar. Check if value is valid: {p1}",
        )
        self.assertLess(
            p1,
            target_pressure + threshold,
            f"p1 is above {target_pressure + threshold:.3f}bar. Check if value is valid: {p1}",
        )
        print(f"Set zero point back to standard value of P1")
        self.bus.f95(self.address, cmd=1)

    def test_f100_read_baud(self):
        data = self.bus.f100(self.address, 0)
        print(f"Test F100 get Data index 0: Para1 = UART, received data: {data}")
        for para, byte in enumerate(data):
            print(f"Para:{para}: {byte}")
        self.assertEqual(
            data[1],
            1,
            "UART settings expected to be 1 -> 115200Baud , no parity, odd parity, 1stop bit",
        )


if __name__ == "__main__":
    unittest.main()
