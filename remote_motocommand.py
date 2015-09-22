#!/usr/bin/env python
""" motocommand: Connect to a YASNAC ERC and send command(s) """
import argparse
import sys

#import yasnac.remote.erc as erc_local
import yasnac.remote.erc as erc
import Pyro4


def main():
    """
    primary function for command-line execution. return an exit status integer
    or a bool type (where True indicates successful exection)
    """
    formatter = argparse.RawDescriptionHelpFormatter
    argp = argparse.ArgumentParser(formatter_class=formatter, description=(
        "Connects to a YASNAC ERC and sends system control command(s)\n"
        "Make sure you quote each command, for example: \n"
        '\nmotocommand "SVON 1" "JWAIT 10" "START TESTJOB"\n'
        "\nAvailable System Control Functions:\n"
        "-----------------------------------\n"
        "CANCEL - Cancels the error status\n"
        "CYCLE n - Selects a motion cycle mode, n is between 1 and 3\n"
        "DELETE j - Deletes the specified job, j is a job name or * \n"
        "HLOCK n - Turns operator's panel interlock on/off, n is 1 or 0\n"
        "HOLD n - Puts a hold on the robot manipulator, n is 1 or 0\n"
        "JSEQ s,n - Set job and line number; s is job name, n is line no.\n"
        "JWAIT n - Wait n sec., return running job status, n is -1 to 32767\n"
        "MDSP s - Displays a message on the console, s is up to 28 chars.\n"
        "RESET - Resets robot alarms\n"
        "SETMJ j - Makes the specified job the master job, j is a job name\n"
        "START j - Starts robot operation. j is a an OPTIONAL job name\n"
        "SVON n - Turns servo power on/off. n is 1 or 0\n"
        "RUFRAME ? - Unknown undocumented function\n"
        "WUFRAME ? - Unknown undocumented function\n"
        "CVTRJ ? - Unknown undocumented function\n"
        "\nAvailable Status Read Functions:\n"
        "--------------------------------\n"
        "RALARM - Lists error and alarm codes\n"
        "RJDIR j - Lists all jobs or subjobs of j, j is * or a job name\n"
        "RJSEQ - Lists the current job name, line number and step number\n"
        "RPOS - Lists the current robot position in rectangular coordinates\n"
        "RPOSJ - Lists the current robot position in joint coordinates\n"
        "RSTATS - Lists the status of several robot conditions\n"))
    argp.add_argument('command', nargs="+", help=(
        "A command to send to the ERC controller"))
    argp.add_argument('-d', '--debug', action="store_true", help=(
        "Enable transaction debugging output"))
    args = argp.parse_args()

    if sys.version_info < (3,0) :
        input = raw_input
    uri = input("Enter the uri of the robot instance: ").strip()
    Pyro4.config.SERIALIZER = "pickle"
    Pyro4.config.SERIALIZERS_ACCEPTED = {"json","marshal","serpent","pickle"}
    robot = Pyro4.Proxy(uri)
    #uri = input("Enter the uri of the robot lib: ").strip()
    #erc = Pyro4.Proxy(uri)
    #robot = erc.ERC()

    #erc.DEBUG = args.debug

    for command in args.command:
        print "about to " + command + " !"
        result = robot.execute_command(command)
        if result:
            print ",".join(result)
            if command == 'RSTATS':
                erc.warn("The result represents these flags: "
                         + ",".join(erc.decode_rstats(result)), True)


    return True


if __name__ == '__main__':
    RESULT = main()
    sys.exit(int(not RESULT if isinstance(RESULT, bool) else RESULT))
