import asyncio
from bleak import BleakScanner
import yaml


async def run():
    info = {}
    devices = await BleakScanner.discover()
    for d in devices:
        print(d)