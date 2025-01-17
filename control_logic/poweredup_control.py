# modified https://pybricks.com/projects/tutorials/wireless/hub-to-device/pc-communication/

# SPDX-License-Identifier: MIT
# Copyright (c) 2020 Henrik Blidh
# Copyright (c) 2022-2023 The Pybricks Authors

"""
Example program for computer-to-hub communication.

Requires Pybricks firmware >= 3.3.0.
"""

import asyncio
from contextlib import suppress
from bleak import BleakScanner, BleakClient

PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"

# Replace this with the name of your hub if you changed
# it when installing the Pybricks firmware.
HUB_NAME = "Pybricks Hub"

class poweredup_control():
    main_task = None
    ready_event = None
    device = None
    client = None


    def __init__(self, device, client, ready_event, main_task):
        self.main_task = main_task
        self.device = device
        self.client = client

        self.ready_event = ready_event

    async def send(self, data):
        ready_event = self.ready_event
        # Wait for hub to say that it is ready to receive data.
        await ready_event.wait()
        # Prepare for the next ready event.
        ready_event.clear()
        # Send the data to the hub.
        await self.client.write_gatt_char(
            PYBRICKS_COMMAND_EVENT_CHAR_UUID,
            b"\x06" + data,  # prepend "write stdin" command (0x06)
            response=True
        )
    async def sendCmd(self, cmdstr: str):
        cmdstr = str.encode(cmdstr)
        cmdlen = str.encode(f"{len(cmdstr):03d}")
        # send length of cmdstr first as header, then send the whole of cmdstr
        await self.send(cmdlen)
        await self.send(cmdstr)
            
        
    async def create(hubname = HUB_NAME):

        ready_event = asyncio.Event()
        main_task = asyncio.current_task()
        def handle_disconnect(_):
            print("Hub was disconnected.")
            # If the hub disconnects before this program is done,
            # cancel this program so it doesn't get stuck waiting
            # forever.

            if not main_task.done():
                main_task.cancel()

        def handle_rx(_, data: bytearray):
            if data[0] == 0x01:  # "write stdout" event (0x01)
                payload = data[1:]
                if payload == b"rdy":
                    print("rdy received")
                    ready_event.set()
                else:
                    print("Received:", payload)
            pass

        # Do a Bluetooth scan to find the hub.
        device = await BleakScanner.find_device_by_name(hubname)
        if device is None:
            print(f"could not find hub with name: {hubname}")
            return
        
        client = BleakClient(device, handle_disconnect, timeout=10)
        await client.connect()
        print("Hub connected")
        await client.start_notify(PYBRICKS_COMMAND_EVENT_CHAR_UUID, handle_rx)
        print("Start the program on the hub now with the button.")

        return poweredup_control(device, client, ready_event, main_task)


        

async def main():
    controls = await poweredup_control.create()
    if controls is None:
        print("not connected")
        exit()
    # for testing purposes only
    async def printSendCmd(cmd):
        print(cmd)
        await controls.sendCmd(cmd)
    await printSendCmd("(A, 200)")
    await asyncio.sleep(5)
    await printSendCmd("(A, 150, 450)|(B, 300, 900)")
    await asyncio.sleep(5)
    await printSendCmd("(A, brake)|(B, brake)")


# Run the main async program.
if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())


