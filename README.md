
# Polar Heart Strap Data Streaming

This project enables streaming of ECG and ACC (acceleration) data from a Polar heart strap using the `bleak` library and asyncio. The data can be streamed directly or sent to a Lab Streaming Layer (LSL) for further analysis or integration with other applications.

## Prerequisites

Before running the project, make sure you have the following dependencies installed:

- Python 3.8 or above (tested with Python 3.8 and above)
- `bleak` library: Install using `pip install bleak`
- `numpy` library: Install using `pip install numpy`
- (Optional) `pylsl` library: Install using `pip install pylsl` if you want to enable LSL streaming

## Usage

1. Clone the repository or download the project files to your local machine.
2. Open a terminal or command prompt and navigate to the project directory.
4. Run the `main.py` script using the command `python main.py -a "polar-mac-address"`.
5. The script will connect to the Polar device and start streaming the ECG and ACC data.
6. If LSL streaming is enabled (`python main.py -a "polar-mac-address" -lsl True`), the data will be sent to the LSL server and can be accessed by other LSL-compatible applications.

**Note:** Ensure that your Polar heart strap is properly woren and discoverable before connecting.

## Configuration

The `main.py` file contains a few configuration options that can be modified:

- `address`: MAC address of the Polar device. By default, it is set to `"E1:26:4D:8F:18:3B"`. Update it with the actual address of your device.
- `lsl`: Set this flag to `True` if you want to enable LSL streaming. By default, it is set to `False`. When set to `True`, the script will attempt to send data to the LSL server.

## Customization

If you want to customize the project further, you can modify the `Polar` class in the `main.py` file. This class handles the Bluetooth communication and data processing. You can add additional functionality or modify the data processing logic according to your requirements.

## Contributing

Contributions to this project are welcome. If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the project repository.

## License

This project is licensed under the [MIT License]. Feel free to use and modify the code as per the terms of the license.

## Acknowledgements

This project relies on the following libraries:

- `bleak`: A Bluetooth Low Energy library for Python
- `numpy`: A library for scientific computing with Python
- `pylsl` (optional): A library for Lab Streaming Layer integration

## Disclaimer

This project is provided as-is, without any warranties or guarantees. The use of this project and any consequences arising from it are solely the responsibility of the user.