# keller-protocol - The KELLER Protocol (Python)

## General Pre-requirement:

* A KELLER device is needed that can communicate with the Serial Port.
* ...with a USB-COM converter cable (eg.K114 series) AND the needed FTDI
  driver (https://www.ftdichip.com/Drivers/VCP.htm)
* ...or directly with a cable of the K-10X series

## Installation

```pip install keller-protocol```  
See https://pypi.org/project/keller-protocol/


## Usage

todo: Hinweise keller_protocol.py + Genereller Ablauf mit Beispiel von 2-3 Aufrufen


## Usage Example with X Line
```python
import keller_protocol
import time


class XLine:
    def __init__(self, port, baud_rate, address, timeout, echo=True):
        self.bus = keller_protocol.KellerProtocol(port, baud_rate, timeout, echo)
        self.address = address
        self.serial_number = None
        self.f73_channels = {
            "CH0": 0,
            "P1": 1,
            "P2": 2,
            "T": 3,
            "TOB1": 4,
            "TOB2": 5,
            "ConTc": 10,
            "ConRaw": 11,
        }
        self.init_f48()

    def init_f48(self) -> str:
        """Initialise and release"""
        answer = self.bus.f48(self.address)
        print(f" Init of Device Address: {self.address} with Firmware: {answer}")

    def get_serial(self) -> int:
        """Get Serial Number from X-Line

        :returns Serial Number
        """
        self.serial_number = self.bus.f69(self.address)
        return self.serial_number

    def get_address(self) -> int:
        return self.address

    def set_address(self, new_address: int) -> int:
        """Change the Device address. -> Has to be unique on the RS485 bus

        :param new_address: New address of the Device
        :return: If successful return new_address otherwise old address and throw exception
        """
        self.address = self.bus.f66(self.address, new_address)
        return self.address

    def measure_tob1(self) -> float:
        """Get temperature TOB1

        :return: temperature
        """
        temperature = self.bus.f73(self.address, self.f73_channels["TOB1"])
        return temperature

    def measure_p1(self) -> float:
        """Get pressure P1

        :return: pressure
        """
        pressure = self.bus.f73(self.address, self.f73_channels["P1"])
        return pressure


if __name__ == "__main__":
    # Example usage:
    # Init transmitter
    transmitter = XLine(
        port="COM17", baud_rate=115200, address=2, timeout=0.2, echo=True
    )
    serial_number = transmitter.get_serial()
    print(f"Transmitter serial number:{serial_number}")
    print("Press CTRL + C to quit")
    while True:
        try:
            p1 = transmitter.measure_p1()
            tob1 = transmitter.measure_tob1()
            print(f"Pressure P1:{p1:.3f} Temperature TOB1:{tob1:.3f}")
            time.sleep(1)
        except KeyboardInterrupt:
            print("Quit!")
            break

```



[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Upload Python Package](https://github.com/KELLERAGfuerDruckmesstechnik/keller_protocol_python/actions/workflows/python-publish.yml/badge.svg)](https://github.com/KELLERAGfuerDruckmesstechnik/keller_protocol_python/actions/workflows/python-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
