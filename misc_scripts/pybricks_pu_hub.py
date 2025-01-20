from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait
from pybricks.tools import multitask, run_task
# Standard MicroPython modules
from usys import stdin, stdout
from uselect import poll
"""
def letter2port(letter):
    # supports A, B, C, D
    letter = letter.lower()
    if letter == 'a':
        return Port.A
    elif letter == 'b':
        return Port.B
    elif letter == 'c':
        return Port.C
    elif letter == 'd':
        return Port.D
    else:
        print(f"{letter} is not a port")
        return None
"""
motors = {
    'A': Motor(Port.A),
    'B': Motor(Port.B)
}
async def motor_run(cmd):
    cmd = cmd[1:-1].split(',')
    #print(f"command: {cmd}")
    curr_motor = motors[cmd[0].upper()]
    if len(cmd) == 2 and isinstance(cmd[1], str) and cmd[1].lower().strip() == "brake":
        curr_motor.brake()
    elif len(cmd) == 2:
        #await curr_motor.run(int(cmd[1]))
        curr_motor.run(int(cmd[1]))
    else:
        await curr_motor.run_angle(int(cmd[1]), int(cmd[2]))

async def run_commands(cmdstr):
    # IMPORTANT: coded for up two motors (A and B)
    # list of strings, each representing command for a motor
    cmds = cmdstr.split('|')
    #print(cmds)
    # start moving motors
    motorruns = []
    
    await multitask(*[motor_run(cmd) for cmd in cmds])

# Optional: Register stdin for polling. This allows
# you to wait for incoming data without blocking.
keyboard = poll()
keyboard.register(stdin)

#run_task(run_commands("(A, 50)|(B, 50, 45)"))

while True:

    # Let the remote program know we are ready for a command.
    stdout.buffer.write(b"rdy")

    # header
    while not keyboard.poll(0):
        # Optional: Do something here.
        wait(1)
    # Read bytes
    cmdlen = int(stdin.buffer.read(3))
    #print(f"command length: {cmdlen}")

    stdout.buffer.write(b"rdy")
    #command string
    while not keyboard.poll(0):
        # Optional: Do something here.
        wait(1)
    # Read bytes
    cmdstr = str(stdin.buffer.read(cmdlen))[2:-1]

    # Formatting of cmd:
    # (port, power or 'brake', <degrees>)|(A, 50)|(B, 50, 45)...
    # e.g (A, 50)|(B, 50, 45)
    #print(cmdstr)
    run_task(run_commands(cmdstr))
    #stdout.buffer.write(b"ran")


   


