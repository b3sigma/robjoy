#!/usr/bin/env python
import argparse
import copy
import sys
import operator
import datetime

import pygame
from pygame.locals import *

import yasnac.remote.erc as erc
import Pyro4

class LocalJoystick :
    def __init__(self, **args) :
        pygame.init()
        pygame.display.set_caption("Robot Joystick Controller")

        self._messages = []
        self._messages.append("woo!")

        self.InitJoystick()

        if (self._joy == None) :
            return
        #

        self.InitRobotState(args['remote'], args['speed'])

        self._screen = pygame.display.set_mode((1000,800))
        self._font = pygame.font.SysFont("Courier", 20)
        self._running = True
    #

    def InitJoystick(self) :
        pygame.joystick.init()
        self._joy = None
        self._joy_state = {}

        if(pygame.joystick.get_count() == 0) :
            return
        #

        # try the first one for the moment to keep ui minimal
        self._joy = pygame.joystick.Joystick(0)
        self._joy.init()

        #so it seems like all axis are -1.0 to 1.0 from pygame

        self._bindings = { \
            "Axis0": { "target": 0, "speed" : 0.001, "dead" : 0.1 }, \
            "Axis1": { "target": 1, "speed" : 0.001, "dead" : 0.1 }, \
#            "Axis2": { "target": 2, "speed" : 0.01, "dead" : 0.1 }, \
            "Axis3": { "target": 3, "speed" : 0.001, "dead" : 0.1 }, \
            "Axis4": { "target": 4, "speed" : 0.001, "dead" : 0.1 }, \
            "Button4": { "target": 5, "speed": -0.01, "dead" : 0.5 }, \
            "Button5": { "target": 5, "speed": 0.01, "dead" : 0.5 }, \
            }
        self._cmd_bindings = { \
            "Button6": { "remote": True, "cmd_cursor": 1, "cmds": [ "SVON 0", "SVON 1" ], }, \
            "Button7": { "remote": False, "cmd_cursor": 0, "cmds": [ "RPOSReset"], }, \
            }
        
    #

    def ExecuteLocalBinding(self, command) :
        if command == "RPOSReset" :
            self.DoRPOSReset()
        #
    #       

    def DoRPOSReset(self) :
        result = self._robot.execute_command("RPOS")
        if not result:
            self._running = False
        else :
            self._messages.append(str(result))
            for i in range(0, len(self._robot_state)) :
                if(i >= len(result)) :
                    break;
                #
                self._robot_state[i]["cur"] = float(result[i])
                if(float(result[i]) < self._robot_state[i]["min"]) :
                    self._robot_state[i]["min"] = float(result[i])
                if(float(result[i]) > self._robot_state[i]["max"]) :
                    self._robot_state[i]["max"] = float(result[i])
                self._last_robot_state = copy.deepcopy(self._robot_state)
            #
        #
    #

    def InitRobotState(self, remote, speed) :
        # values from experiment so far
        self._robot_state = { \
            0 : { "cur" : 0.0, "min" : -1000.0, "max" : 1000.0 }, \
            1 : { "cur" : 0.0, "min" : -1000.0, "max" : 1000.0 }, \
            2 : { "cur" : 0.0, "min" : -1000.0, "max" : 1000.0 }, \
            3 : { "cur" : 0.0, "min" : -1000.0, "max" : 1000.0 }, \
            4 : { "cur" : 0.0, "min" : -1000.0, "max" : 1000.0 }, \
            5 : { "cur" : 0.0, "min" : -1000.0, "max" : 1000.0 },
            }

        self._robot_commands = []

        self._speed = speed
        self._messages.append("speed was " + str(self._speed))

        self._next_robot_tick = pygame.time.get_ticks() # now

        if sys.version_info < (3,0) :
            input = raw_input
        #

        if remote == None :
            # do local
            self._robot = erc.ERC()
        else :
            Pyro4.config.SERIALIZER = "pickle"
            Pyro4.config.SERIALIZERS_ACCEPTED = {"json","marshal","serpent","pickle"}

            uri = remote
            if len(uri) <= 1 :
                uri = input("Enter the uri of the robot: ").strip()
            #
            self._robot = Pyro4.Proxy(uri)
        #

        self.DoRPOSReset()
    #

    

    def ApplyJoyState(self, deltaTime) :
        for (name, binding) in self._bindings.iteritems() :
            robot_axis = self._robot_state[binding["target"]]

            joy = self._joy_state[name]
            joy_curr = joy["cur"]
            if abs(joy_curr) < binding["dead"] :
                continue
            #

            delta = binding["speed"] * deltaTime * joy_curr
            robot_axis["cur"] = robot_axis["cur"] + delta
            if (robot_axis["cur"] > robot_axis["max"]) :
                robot_axis["cur"] = robot_axis["max"]
            #
            if (robot_axis["cur"] < robot_axis["min"]) :
                robot_axis["cur"] = robot_axis["min"]
            #

            #update the state
            self._robot_state[binding["target"]] = robot_axis
        #

        for (name, binding) in self._cmd_bindings.iteritems() :
            joy = self._joy_state[name]
            joy_cur = joy["cur"]

            if joy_cur > 0 :
                last_cur = None
                if name in self._prev_joy_state :
                    last_joy = self._prev_joy_state[name]
                    last_cur = last_joy["cur"]
                #

                if joy_cur != last_cur :
                    if len(binding["cmds"]) > 0 :
                        if binding["remote"] == True :
                            self._robot_commands.append(binding["cmds"][binding["cmd_cursor"]])
                        else :
                            self.ExecuteLocalBinding(binding["cmds"][binding["cmd_cursor"]])
                        #
                        binding["cmd_cursor"] = (binding["cmd_cursor"] + 1) % len(binding["cmds"])
                    #
                #
            #
        #
    #

    def ApplyRobotState(self) :

        #send commands immediately, don't wait on the tick
        for cmd in self._robot_commands :
            result = self._robot.execute_command(cmd)
            self._messages.append("executed '" + str(cmd) + "' for result " + str(result))
        #
        self._robot_commands = []

        self._robot_tick_interval = 100
        if (pygame.time.get_ticks() > self._robot_tick_interval + self._next_robot_tick) :
            self._next_robot_tick = pygame.time.get_ticks()

            # can't send a move command if we are already there or it will alarm

            skip_send = True
            pos_threshold = 0.01 # need a position delta larger than this, somewhere
            for i in range(0, len(self._robot_state)) :
                delta = abs(self._robot_state[i]["cur"] - self._last_robot_state[i]["cur"])
                if(delta > pos_threshold) :
                    skip_send = False
                    break # only need the one
                #
            #

            if skip_send == True :
                return
            #
            
            self._move_type = "MOVL" # "MOVJ" # "MOVL" 

            #self._speed = 20.0
            command = self._move_type \
                + " 0," + str(self._speed) + ",0," \
                + str(self._robot_state[0]["cur"]) + "," \
                + str(self._robot_state[1]["cur"]) + "," \
                + str(self._robot_state[2]["cur"]) + "," \
                + str(self._robot_state[3]["cur"]) + "," \
                + str(self._robot_state[5]["cur"]) + "," \
                + str(self._robot_state[4]["cur"]) + "," \
                + "0,0,0,0,0,0,0,0"

            self._last_robot_state = copy.deepcopy(self._robot_state)

            self._messages.append(command)
            result = self._robot.execute_command(command)
            self._messages.append(str(result))
            #robot.execute_command(("MOVL 0,{speed},0,{pos},"
            #               "0,0,0,0,0,0,0,0").format(speed=speed_string,
            #                                         pos=target_string))
        #
    #

    def UpdateJoyState(self) :
        self._key_events = pygame.event.get()

        for event in self._key_events :
            if (event.type == KEYDOWN and event.key == K_ESCAPE) :
                self.Quit()
                return
            #
            if (event.type == QUIT) :
                self.Quit()
                return
            #
        #

        if(self._joy == None) :
            return
        #

        self._prev_joy_state = copy.deepcopy(self._joy_state)

        self._joy_state = {}
        for i in range(0, self._joy.get_numaxes()) :
            axis_name = "Axis" + str(i)

            max_min_state = {"max" : 0, "min" : 0, "cur" : 0}
            if (axis_name in self._prev_joy_state) :
                max_min_state = self._prev_joy_state[axis_name]
            #

            current_state = self._joy.get_axis(i)
            max = current_state
            if ("max" in max_min_state) :
                max = max_min_state["max"]
            #
            min = current_state
            if ("min" in max_min_state) :
                min = max_min_state["min"]
            #

            if(current_state >= max) :
                max_min_state["max"] = current_state
            if(current_state <= min) :
                max_min_state["min"] = current_state
            #

            max_min_state["cur"] = current_state
            self._joy_state[axis_name] = max_min_state
        #
        
        for i in range(0, self._joy.get_numbuttons()) :
            button_name = "Button" + str(i)
            
            state = {}
            state["min"] = 0
            state["max"] = 1
            state["cur"] = self._joy.get_button(i)
            
            self._joy_state[button_name] = state
        #
    #

    def DrawText(self, text, leftOffset, topOffset, color) :
        surface = self._font.render(text, True, color, (0,0,0))
        surface.set_colorkey((0,0,0))
        self._screen.blit(surface, (leftOffset, topOffset))
    #

    def DrawState(self) :
        self._screen.fill(0)

        xOffset = 10
        yOffset = 10
        yLine = 20
        if (self._joy_state == None) :
            self.DrawText("No joystick?", xOffset, yOffset, (255, 255, 255))
            return
        #

        for (target,state) in self._robot_state.iteritems() :
            text = "RobotIndex(%d) max(%f) min(%f) cur(%f)" % (target, state["max"], state["min"], state["cur"])
            self.DrawText(text, xOffset, yOffset, (255,255,255))
            yOffset += yLine
        #
        
        self.DrawText("Axes (%d)" % len(self._joy_state), xOffset, yOffset, (255, 255, 255))
        yOffset += yLine
        
        for (name,state) in self._joy_state.iteritems() :
            text = "Name(%s) max(%f) min(%f) cur(%f)" % (name, state["max"], state["min"], state["cur"])
            self.DrawText(text, xOffset, yOffset, (255,255,255))
            yOffset += yLine
        #

        for msg in self._messages :
            self.DrawText(msg, xOffset, yOffset, (255,255,255))
            yOffset += yLine
        #
        max_messages = 10
        if(len(self._messages) > max_messages) :
            self._messages = self._messages[(len(self._messages) - max_messages):len(self._messages)]
        #

        pygame.display.flip()
    #


    def MainLoop(self) :
        self._last_tick = pygame.time.get_ticks()
        while (self._running == True) :
            self._delta_time = self._last_tick - pygame.time.get_ticks()
            self._last_tick = pygame.time.get_ticks()
            if (self._delta_time <= 0) :
                self._delta_time = 16 #60 hz default
            #
            self.UpdateJoyState()
            self.ApplyJoyState(self._delta_time)
            self.ApplyRobotState()
            self.DrawState()

        #
    #

    def Quit(self) :
        pygame.display.quit()
        self._running = False
    #
#

def main() :
    formatter = argparse.RawDescriptionHelpFormatter
    argp = argparse.ArgumentParser(formatter_class=formatter, description=(
        "Uses a joystick to send commands to the YASNAC robot\n"))
    argp.add_argument('-r', '--remote', nargs='?', const='')
    argp.add_argument('-s', '--speed', default='0.5')
    args = argp.parse_args()

    robotJoystick = LocalJoystick(remote=args.remote, speed=args.speed)
    robotJoystick.MainLoop()
#

main()
