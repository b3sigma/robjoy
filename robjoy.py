#!/usr/bin/env python
import pygame
from pygame.locals import *

class LocalJoystick :
    def __init__(self) :
        pygame.init()
        pygame.display.set_caption("Robot Joystick Controller")
        
        self.InitJoystick()
        
        if (self._joy == None) :
            return
        #
            
        self.InitRobotState()
        
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
            "Axis0": { "target": 0, "speed" : 0.01, "dead" : 0.1 }, \
            "Axis1": { "target": 1, "speed" : 0.01, "dead" : 0.1 }, \
            "Axis2": { "target": 2, "speed" : 0.01, "dead" : 0.1 }, \
            "Axis3": { "target": 3, "speed" : 0.01, "dead" : 0.1 }, \
            "Axis4": { "target": 4, "speed" : 0.01, "dead" : 0.1 } }
    #
    
    def InitRobotState(self) :
        self._robot = { \
            0 : { "curr" : 0.0, "min" : -100.0, "max" : 100.0 }, \
            1 : { "curr" : 0.0, "min" : -100.0, "max" : 100.0 }, \
            2 : { "curr" : 0.0, "min" : -100.0, "max" : 100.0 }, \
            3 : { "curr" : 0.0, "min" : -100.0, "max" : 100.0 }, \
            4 : { "curr" : 0.0, "min" : -100.0, "max" : 100.0 } }
        
        self._next_robot_tick = pygame.time.get_ticks() # now
        #todo: connecto, parso,
    #
    
    def ApplyJoyState(self, deltaTime) :
        for i in range(0, self._joy.get_numaxes()) :
            axis_name = "Axis" + str(i)
            
            binding = self._bindings[axis_name]
            robot_axis = self._robot[binding["target"]]
            
            joy = self._joy_state[axis_name]
            joy_curr = joy["curr"]
            if abs(joy_curr) < binding["dead"] :
                continue
            #
            
            delta = binding["speed"] * deltaTime * joy_curr
            robot_axis["curr"] = robot_axis["curr"] + delta 
            if (robot_axis["curr"] > robot_axis["max"]) :
                robot_axis["curr"] = robot_axis["max"]
            #
            if (robot_axis["curr"] < robot_axis["min"]) :
                robot_axis["curr"] = robot_axis["min"]
            #
            
            #update the state
            self._robot[binding["target"]] = robot_axis           
        #
    #
    
    def ApplyRobotState(self) :
        self._next_robot_tick = pygame.time.get_ticks()

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
        
        self._prev_joy_state = self._joy_state
        
        self._joy_state = {}
        for i in range(0, self._joy.get_numaxes()) :
            axis_name = "Axis" + str(i)
            
            max_min_state = {"max" : 0, "min" : 0, "curr" : 0}
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
             
            max_min_state["curr"] = current_state
            self._joy_state[axis_name] = max_min_state
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
        
        for (target,state) in self._robot.iteritems() :
            text = "RobotIndex(%d) max(%f) min(%f) curr(%f)" % (target, state["max"], state["min"], state["curr"])
            self.DrawText(text, xOffset, yOffset, (255,255,255))
            yOffset += yLine
        
        self.DrawText("Axes (%d)" % len(self._joy_state), xOffset, yOffset, (255, 255, 255))
        yOffset += yLine
        
        for (name,state) in self._joy_state.iteritems() :
            text = "Name(%s) max(%f) min(%f) curr(%f)" % (name, state["max"], state["min"], state["curr"])
            self.DrawText(text, xOffset, yOffset, (255,255,255))
            yOffset += yLine
        #
        
        pygame.display.flip()
    #
               
    
    def main(self) :
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

robotJoystick = LocalJoystick()
robotJoystick.main()