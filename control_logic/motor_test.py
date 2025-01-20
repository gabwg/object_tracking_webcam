import asyncio
from contextlib import suppress
from control_logic.motor_control.poweredup_control import poweredup_control


async def main():
    controls = await poweredup_control.create()
    if controls is None:
        print("not connected")
        exit()
    # for testing purposes only
    async def printSendCmd(cmd):
        print(cmd)
        await controls.sendCmd(cmd)

    while True:
        command = input("Input command:\n")
        if command == "seq1":
            await printSendCmd("(A, 100, 100)|(B, 100, 200)")
            await printSendCmd("(A, 100, -100)|(B, 100, -200)")
        elif command == "seq2":
            await printSendCmd("(A, 300, 200)|(B, 300, 400)")
            await printSendCmd("(A, 300, -200)|(B, 300, -400)")

        else:
            await printSendCmd(command)
    


# Run the main async program.
if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())


