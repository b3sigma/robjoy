#!/usr/bin/env python
""" motomotion: Connect to an ERC-series robot and move the manipulator """
import argparse
import sys
import operator
import datetime

import yasnac.remote.erc as erc
import Pyro4

MATHOPS = {"+=": operator.add,
           "-=": operator.sub,
           "*=": operator.mul,
           "/=": operator.truediv,
           "^=": operator.pow}


def resolve_maths(given, current_value):
    """
    If the given input starts with a math operator symbol, perform that
    operation on the current value. All numbers, including the return value
    will be converted to floats with 3 decimal places. If there is no operator
    symbol, return the input. Examples:
    resolve_maths("/2", 5) will return "2.500"
    resolve_maths("2", "5") will return "2.000"
    """
    result = given

    if given[0:2] in MATHOPS:
        a = float(current_value)
        b = float(given[2:].strip())
        operation = MATHOPS[given[0:2]]
        result = operation(a, b)

    return "{:.3f}".format(float(given))



def main():
    """
    primary function for command-line execution. return an exit status integer
    or a bool type (where True indicates successful exection)
    """
    argp = argparse.ArgumentParser(description=(
        "Connect to an ERC-series robot and move the manipulator"), epilog=(
        'If you see a "too few arguments" error, try adding "--" before '
        "your position argument. For example: "
        'motomove -- "coordinates"'))
    argp.add_argument('--speed', nargs="?", type=float, default=10.0, help=(
        "The speed at which the robot is to perform the motion, in mm/s. "
        "Allowable values are from 0.1 to 1200.00. The default is a glacial "
        "and safeish 10.0. BE SAFE."))
    argp.add_argument('--power', choices=('on', 'off', 'onoff'), help=(
        'Controls servo power; a value of "on" will activate servo power '
        'in order to perform the motion, a value of "off" will turn the '
        'servo power off after performing the motion, a value of "onoff" '
        'will both activate the servo power before the motion and deactivate '
        'the servo power after the motion is complete. The default is not to '
        'make any change to the state of servo power.'))
    argp.add_argument('-d', '--debug', action="store_true", help=(
        "Enable transaction debugging output"))
    argp.add_argument('position', help=(
        "The position to move the robot into. Must be in rectangular "
        "coordinates and comma separated: x,y,z,tx,ty,tz. tx,ty,tz are tool "
        "list angles in degrees. If you don't want to specify a particular "
        'value, leave it empty. You can specify deltas, such as '
        "+=10.1,-=5,/=3,*=2 for movement relative to the robot's current "
        "position. NOTE: The resulting values won't be sanity-checked!"))
    args = argp.parse_args()

    #erc.DEBUG = args.debug

    # sanity check
    if not (0.1 <= args.speed <= 1200.0):
        print "Invalid speed value, must be between 0.1 and 1200.0"
        return False

    speed_string = "{:.2f}".format(args.speed)

    if sys.version_info < (3,0) :
        input = raw_input
    uri = input("Enter the uri of the robot: ").strip()
    Pyro4.config.SERIALIZER = "pickle"
    Pyro4.config.SERIALIZERS_ACCEPTED = {"json","marshal","serpent","pickle"}
    robot = Pyro4.Proxy(uri)
    # now actually do stuff
    #robot = erc.ERC()

    # Calculate the 6 target coordinates based on the given argument and
    # the current position of the robot
    target = robot.execute_command("RPOS")[0:6]  # retrieve the current pos.
    for index, coordinate in enumerate(args.position.split(',')[:6]):
        if coordinate:
            target[index] = resolve_maths(coordinate.strip(), target[index])

    target_string = ",".join(target)

    # are the robot servos on?
    rstats = erc.decode_rstats(robot.execute_command("RSTATS"))
    if not "servos on" in rstats:
        if args.power in ('on', 'onoff'):
            # Turn them on
            robot.execute_command("SVON 1")
            # fixme: error checking
        else:
            erc.warn("Cannot move the manipulator when the servos are off",
                     force=True)
            return False

    print "moving to {} at {} mm/s".format(target_string, speed_string)

    robot.execute_command(("MOVL 0,{speed},0,{pos},"
                           "0,0,0,0,0,0,0,0").format(speed=speed_string,
                                                     pos=target_string))
    robot.execute_command("JWAIT -1")

    # shoule we turn off the servos?
    if args.power in ('off', 'onoff'):
        # Turn them off
        robot.execute_command("SVON 0")

    return True


if __name__ == '__main__':
    RESULT = main()
    sys.exit(int(not RESULT if isinstance(RESULT, bool) else RESULT))
