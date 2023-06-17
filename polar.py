import asyncio
import os
from bleak.uuids import uuid16_dict
from bleak import BleakClient
import signal
import logging
import sys
import numpy as np
import time
import math



from typing import Any

# HIL 

import numpy as np

def convert_array_to_signed_int(data: np.ndarray, offset: int, length: int) -> int:
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=True,
    )


def convert_to_unsigned_long(data: np.ndarray, offset: int, length: int) -> int:
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=False,
    )

    # Need to find a way to make this more dynamic
if os.environ.get("LSL_STREAMMING") == str(1):
    from pylsl import StreamInfo, StreamOutlet
    import pylsl

    def ECG_stream(name:str, sampling_frq:int = 130) -> StreamOutlet:
        info = StreamInfo(name, 'ECG', 1, sampling_frq, 'float32', 'myuid2424') #type: ignore
        info.desc().append_child_value("manufacturer", "Polar")
        channels = info.desc().append_child("channels")
        for c in ["ECG"]:
            channels.append_child("channel")\
                .append_child_value("name", c)\
                .append_child_value("unit", "microvolts")\
                .append_child_value("type", "ECG")
        return StreamOutlet(info, 74)

    def ACC_stream(name:str, sampling_frq:int  = 200) -> StreamOutlet:
        info = StreamInfo(name, 'ACC', 3, sampling_frq, 'float32', 'myuid2425') #type: ignore
        info.desc().append_child_value("manufacturer", "Polar")
        channels = info.desc().append_child("channels")
        for c in ['X', 'Y', 'Z']:
            channels.append_child("channel")\
                .append_child_value("name", c)\
                .append_child_value("unit", "mg")\
                .append_child_value("type", "ACC")
        return StreamOutlet(info, 32)



class Polar(object):
    def __init__(self, address:str = "E1:26:4D:8F:18:3B", ECG: bool= True, ACC: bool = True, 
            publish_dashboard:bool = True, acc_name : str = 'polar accel', ecg_name : str = 'polar ECG' ) -> None:
        """_Main polar acquisition function which uses the Bluetooth ble to get the data. Depends on the Bluez library

        Args:
            address (str, optional): BLE address for the polar device. Defaults to "E1:26:4D:8F:18:3B".
            ECG (bool, optional): ECG data collection flag . Defaults to True.
            ACC (bool, optional): Acceleration data collection flag. Defaults to True.
            publish_dashboard (bool, optional): Should the data be published. Defaults to True.
            acc_name (str, optional): Name of the acceleration stream. Defaults to 'polar accel'.
            ecg_name (str, optional): Name of the ECG stream. Defaults to 'polar ECG'.
        """
        # address
        self.ADDRESS = address

        # flag
        self.ECG_FLAG = ECG
        self.ACC_FLAG = ACC
        self.PUBLISH_DASHBOARD = publish_dashboard

        # dict
        self.ECG_data = {}
        self.ECG_data['ecg'] = []
        self.ECG_data['time'] = []
        self.ACC_data = {}
        self.ACC_data['acc'] = []
        self.ACC_data['time'] = []

        # logging
        self.logger = logging.getLogger(__name__)

        # time
        self.previous_time = 0
        self.previous_time_ecg = 0

        # placeholder
        self.client = None

        # setup
        self._setup()

        # Need to find a way to make this more dynamic
        if os.environ.get("LSL_STREAMMING") == str(1):

            # ACC stream
            self.ACC_stream = ACC_stream(acc_name)
            # ECG stream
            self.ECG_stream = ECG_stream(ecg_name)



    def _setup(self) -> None:
        """Setup the streaming and connect the device to the bluetooth
        """
        uuid16_dict_polar = {v: k for k, v in uuid16_dict.items()}

        ## This is the device MAC ID, please update with your device ID

        ## UUID for model number ##
        self.MODEL_NBR_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
            uuid16_dict_polar.get("Model Number String")
            )


        ## UUID for manufacturer name ##
        self.MANUFACTURER_NAME_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
            uuid16_dict_polar.get("Manufacturer Name String")
        )

        ## UUID for battery level ##
        self.BATTERY_LEVEL_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
            uuid16_dict_polar.get("Battery Level")
        )

        ## UUID for connection establsihment with device ##
        self.PMD_SERVICE = "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8"

        ## UUID for Request of stream settings ##
        self.PMD_CONTROL = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"

        ## UUID for Request of start stream ##
        self.PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"

        # load all the write data byte arrays
        self.WRITE_DATA = {'ECG':
                           bytearray([0x02, 0x00, 0x00, 0x01, 0x82, \
                                      0x00, 0x01, 0x01, 0x0E, 0x00]),
                           'ACC':bytearray(
                               [0x02,
                                0x02,
                                0x00,
                                0x01,
                                0xC8,
                                0x00,
                                0x01,
                                0x01,
                                0x10,
                                0x00,
                                0x02,
                                0x01,
                                0x08,
                                0x00])
                           }

        ## For Plolar H10  sampling frequencies ##
        self.SAMPLING_FREQ = {'ECG': 130, 'ACC': 200}

    async def main(self):
        try:
            async with BleakClient(self.ADDRESS) as client:
                signal.signal(signal.SIGINT, self._interrupt_handler)
                tasks = [
                    asyncio.ensure_future(self._run(client)),
                ]

                await asyncio.gather(*tasks)
        except:
            print("Device not found, please use the bleak_discover.py command to find the device")
            pass


    async def _run(self, client: BleakClient, debug:bool = False) -> None:
        """Async function with connect to the ble client and initiaing data collection module

        Args:
            client (BleakClient): Bluetooth data collection client.
            debug (bool, optional): debugging the ble system (Not used). Defaults to False.
        """

        ## Writing chracterstic description to control point for request of UUID (defined above) ##
        await client.is_connected() #type: ignore
        self.logger.info("--------- Polar Device connected--------------")

        model_number = await client.read_gatt_char(self.MODEL_NBR_UUID)
        self.logger.info("Model Number: {0}".format("".join(map(chr, model_number))))

        manufacturer_name = await client.read_gatt_char(self.MANUFACTURER_NAME_UUID)
        self.logger.info("Manufacturer Name: {0}".format("".join(map(chr, manufacturer_name))))

        battery_level = await client.read_gatt_char(self.BATTERY_LEVEL_UUID)
        self.logger.info("Battery Level: {0}%".format(int(battery_level[0])))

        att_read = await client.read_gatt_char(self.PMD_CONTROL)

        print(f"connected")


        if self.ACC_FLAG:
            self.logger.info(f'started the acceleration connection')
            await client.write_gatt_char(self.PMD_CONTROL, self.WRITE_DATA['ACC'], response  = True)
            self.logger.info(f'Finished the acceleration connection')
        if self.ECG_FLAG:
            self.logger.info(f'started the ECG connection')
            await client.write_gatt_char(self.PMD_CONTROL, self.WRITE_DATA['ECG'], response = True)
            self.logger.info(f'Finished the ECG connection')

        ## ECG stream started
        await client.start_notify(self.PMD_DATA, self._send_data)

        while True:

            ## While loop, to keep the connection alive ##
            ## Can be used to save the data in a file ##
            await asyncio.sleep(1)
            # printing something for viewer confidence ;)
            print( time.time() - self.previous_time)




    def _interrupt_handler(self, signum: Any, frame: Any) -> None:
        """Handle any interrupt in the data communication

        Args:
            signum (Any): Async interupt handlers
            frame (Any): exit frame
        """
        if self.client is None:
            self.logger.info('no ble client found closing the device')
            sys.exit()
        else:
            self.logger.info('found ble client stopping')
            # close the connection properly
            self.client.disconnect()
            sys.exit()


    def _send_data(self, sender: Any, data: Any) -> None:
        """From the collected data send the ECG and or ACC data to the pylsls

        Args:
            sender (Any): Sender information
            data (Any): Data byte information
        """


        # ECG data
        if data[0] == 0x00:
            timestamp = convert_to_unsigned_long(data, 1, 0)
            step = 3
            samples = data[10:]
            offset, i = 0, 0 
            time_diff = time.time() - self.previous_time_ecg
            ECG_list = []
            while offset < len(samples):
                i += 1
                ecg = convert_array_to_signed_int(samples, offset, step)
                offset += step
                self.ECG_data['ecg'].extend([ecg])
                self.ECG_data['time'].extend([timestamp])
                ECG_list.append(ecg)
            self.previous_time_ecg = time.time()
            # Need to find a way to make this more dynamic
            if os.environ.get("LSL_STREAMMING") == str(1):
                self.ecg_outlet.push_chunk(ECG_list, timestamp)
            self.ECG_stream.push_chunk(ECG_list, pylsl.local_clock() - time_diff)

        # ACC data

        if data[0] == 0x02:
            timestamp = convert_to_unsigned_long(data, 1, 8)
            frame_type = data[9]
            resolution = (frame_type + 1)*8
            step = math.ceil(resolution / 8.0)
            samples = data[10:]
            offset, i = 0, 0 
            time_diff = time.time() - self.previous_time
            ACC_list = []
            while offset < len(samples):
                i += 1
                x = convert_array_to_signed_int(samples, offset, step)
                offset += step
                y = convert_array_to_signed_int(samples, offset, step)
                offset += step
                z = convert_array_to_signed_int(samples, offset, step)
                offset += step
                ACC_list.append([x,y,z])
                self.ACC_data['acc'].extend([[x,y,z]])
                self.ACC_data['time'].extend([timestamp])
            # Need to find a way to make this more dynamic
            if os.environ.get("LSL_STREAMMING") == str(1):
                self.ACC_stream.push_chunk(ACC_list, pylsl.local_clock() - time_diff)
            self.previous_time = time.time()
