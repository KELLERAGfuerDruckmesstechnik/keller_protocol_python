import serial
import struct


class KellerProtocol:
    def __init__(
            self, port: str, baud_rate: int, timeout: float = 0.2, echo: bool = True
    ):
        self.serial = serial.Serial(
            port=port,
            baudrate=baud_rate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=timeout,
        )
        self.echo = echo
        self.serial.close()

    def f30(self, address: int, coeff_no: int) -> float:
        """Function F30: Read Coefficients in IEEE754 format

        :param address: Device address
        :param coeff_no: Coefficient number to read
        :return: value: floating point
        """
        command = [address, 30, coeff_no]
        answer = self._send_receive(command, 8)
        value = struct.unpack(">f", answer[2:6])[
            0
        ]  # '>f' -> big-endian 'f' -> small endian
        return value

    def f31(self, address: int, coeff_no: int, value: float):
        """Function F31: Write Coefficients

        :param address: Device address
        :param coeff_no: Coefficient number to write
        :param value: Value to write to device (Float)
        """
        command = [address, 31, coeff_no]
        # typecast floating value to a list of bytes
        value_bytes = list(struct.pack(">f", value))
        command.extend(value_bytes)
        self._send_receive(command, 5)

    def f32(self, address: int, coeff_no: int) -> int:
        """Function F32: Read out configuration

        :param address: Device address
        :param coeff_no: Index to read
        :return value: 16bit Int
        """
        command = [address, 32, coeff_no]
        answer = self._send_receive(command, 5)
        value = list(answer)[2]
        return value

    def f33(self, address: int, coeff_no: int, value: int):
        """Function F33: Write configuration

        :param address: Device address
        :param coeff_no: Index to write
        :param value: Value to write to device (byte)
        """
        if value > 255:
            raise ValueError
            # raise Exception(f'Incorrect value for F33 configuration:{value} has to be lower than 256')
        command = [address, 33, coeff_no, value]
        self._send_receive(command, 5)

    def f48(self, address: int) -> str:
        """Function 48: Initialise and release

        :param address: Device address
        :return Firmware string
        """
        command = [address, 48]
        answer = self._send_receive(command, 10)
        answer = list(answer)  # typecast to a list
        firmware_class = answer[2]
        firmware_group = answer[3]
        firmware_year = answer[4]
        firmware_week = answer[5]
        return f"{firmware_class}.{firmware_group}-{firmware_year}.{firmware_week}"

    def f66(self, address: int, new_address: int) -> int:
        """Function 66: Write and read new device address

        :param address: old device address
        :param new_address: new device address
        :return: Address of the device is returned as confirmation
        """
        if new_address > 255:
            raise ValueError(
                f"Incorrect new address for Device. Must be smaller than 256"
            )
        if new_address <= 0 and address != 250:
            raise ValueError(f"Incorrect new address for Device. Must be bigger than 0")
        command = [address, 66, new_address]
        answer = self._send_receive(command, 5)
        new_address_from_device = list(answer)[2]

        if new_address_from_device != new_address and address != 250:
            raise Exception(f"Device address {new_address} is already in use")

        return new_address_from_device

    def f69(self, address: int) -> int:
        """Function 69: Read serial number

        :param address: Device address
        :return serial_nr: Serial number of the device
        """
        command = [address, 69]
        answer = self._send_receive(command, 8)
        serial_nr = int.from_bytes(answer[2:6], byteorder="big", signed=False)
        return serial_nr

    def f73(self, address: int, channel: int) -> float:
        """Function 73: Read value of a channel (floating point)

        :param address: Device address
        :param channel: 0:CH0, 1:P1, 2:P2, 3:T, 4:TOB1, 5:TOB2, 10:ConTc, 11:ConRaw
        :return value: floating point
        """
        if channel > 255:
            raise ValueError(
                f"Incorrect value for F73 configuration:{channel} has to be lower than 256"
            )
        command = [address, 73, channel]
        answer = self._send_receive(command, 9)
        value = struct.unpack(">f", answer[2:6])[
            0
        ]  # '>f' -> big-endian 'f' -> small endian
        return value

    def f74(self, address: int, channel: int) -> int:
        """Function 74: Read value of a channel (32bit integer)

        :param address: Device address
        :param channel: 0:CH0, 1:P1, 2:P2, 3:T, 4:TOB1, 5:TOB2, 10:ConTc, 11:ConRaw
        :return value: int32
        """
        if channel > 255:
            raise ValueError(
                f"Incorrect value for F74 configuration:{channel} has to be lower than 256"
            )
        command = [address, 74, channel]
        answer = self._send_receive(command, 9)
        return int.from_bytes(answer[2:6], byteorder="big", signed=True)

    def f95(self, address: int, cmd: int, value=None):
        """Function 95: Commands for setting the zero point

        :param address: Device address
        :param cmd: Which channel to set to certain value
        :param value: ...the certain value
        """
        if cmd > 255:
            raise ValueError(
                f"Incorrect value for F95 command:{cmd} has to be lower than 256"
            )
        command = [address, 95, cmd]
        if value:
            # typecast floating value to a list of bytes
            coeff_no = list(struct.pack(">f", value))
            command.extend(coeff_no)
        self._send_receive(command, 5)

    def f100(self, address: int, index: int):
        """Function 100: Read Configuration

        Please use Function 32 instead of this function for devices of Class.Group-version 5.20-5.24 and earlier.
        With Function 32/33 you have access to a single parameter instead of all five parameters
        :param address: Device address
        :param index: Which parameter Index you would like to read
        :return: 5 parameter
        """
        if index > 255:
            raise ValueError(
                f"Incorrect value for F100 index:{index} has to be lower than 256"
            )
        command = [address, 100, index]
        answer = self._send_receive(command, 9)
        return answer[2:7]

    def _send_receive(self, command: list, read_byte_count: int):
        """send a command and receive a message

        :param command: sending command
        :param read_byte_count: amount of bytes to send
        :return: answer from the device
        """
        crc = self._crc16(command, len(command))
        command.extend(crc)
        self.serial.open()
        self.serial.reset_input_buffer()
        if self.serial is None:
            raise ConnectionRefusedError
        try:
            self.serial.write(command)
        except Exception as e:
            raise ConnectionError(f"Error in sending/reading Keller Protocol: {e}")
        else:
            # Check if the echo is correct
            if self.echo:
                echo_answer = self.serial.read(len(command))
                if command != list(echo_answer):
                    raise Exception("Echo not present")

            answer = self.serial.read(read_byte_count)
            if not answer:
                raise ConnectionRefusedError(
                    f"Device with address {command[0]} did not respond"
                )
            #  Check CRC16 of answer:
            self._raise_on_crc16_missmatch(answer)
            #  Check for Device Errors:
            if list(answer)[1] > 127:
                raise Exception(f"Device Error number: {list(answer)[1]}")
            return answer
        finally:
            self.serial.close()

    def _raise_on_crc16_missmatch(self, buffer: bytes):
        """Check if the Correct CRC16 was sent/received

        :param buffer: Message to check the CRC16
        """
        #  Check CRC16 of answer
        buffer = list(buffer)  # convert to a list
        buffer_crc16 = buffer[-2:]  # last two elements -> CRC16
        buffer_without_crc16 = buffer[: len(buffer) - 2]
        crc_calc = self._crc16(buffer_without_crc16, len(buffer_without_crc16))
        if buffer_crc16 != list(crc_calc):
            raise Exception(f"CRC16 Error expected: {buffer_crc16} but got {crc_calc}")

    @staticmethod
    def _crc16(buffer: list, byte_count: int, offset: int = 0) -> bytes:
        """Calculate the CRC16 Value

        :param buffer:
        :param byte_count:
        :param offset:
        :return: crc16
        """
        polynom = 0xA001
        crc = 0xFFFF

        for i in range(byte_count):
            crc = crc ^ buffer[offset + i]

            for n in range(8):
                ex = crc % 2 == 1
                crc = crc // 2
                if ex:
                    crc = crc ^ polynom

        return bytes([(crc >> 8), (crc & 0x00FF)])
