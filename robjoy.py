#!/usr/bin/env python
import pygame
from pygame.locals import *

class LocalJoystick :
    def __init__(self) :
        pygame.init()
        pygame.display.set_caption("Robot Joystick Controller")
        
        self.InitJoystick()
        
        self._screen = pygame.display.set_mode((300,300))
        self._font = pygame.font.SysFont("Courier", 20)
        self._running = True
    
    def InitJoystick(self) :
        pygame.joystick.init()
        self._joy = None
        self._joy_state = None
        
        if(pygame.joystick.get_count() > 0) :
            # try the first one for the moment to keep ui minimal
            self._joy = pygame.joystick.Joystick(0)
            self._joy.init()
        
    def UpdateJoyState(self) :
        self._key_events = pygame.event.get()
        
        for event in self._key_events :
            if (event.type == KEYDOWN and event.key == K_ESCAPE) :
                self.Quit()
                return
            if (event.type == QUIT) :
                self.Quit()
                return
        
        if(self._joy == None) :
            return
        
        self._joy_state = {}
        for i in range(0, self._joy.get_numaxes()) :
            axis_name = "Axis" + str(i)
            print axis_name
            print (self._joy.get_axis(i))
            self._joy_state[axis_name] = self._joy.get_axis(i)
            
    def DrawText(self, text, leftOffset, topOffset, color) :
        surface = self._font.render(text, True, color, (0,0,0))
        surface.set_colorkey((0,0,0))
        self._screen.blit(surface, (leftOffset, topOffset))
        
    def DrawState(self) :
        self._screen.fill(0)
        
        if (self._joy_state == None) :
            self.DrawText("No joystick?", 10, 10, (255, 255, 255))
            return
        
        self.DrawText("Axes (%d)" % len(self._joy_state), 10, 30, (255, 255, 255))
        
        pygame.display.flip()
               
    
    def main(self) :
        while (self._running == True) :
            self.UpdateJoyState()
            self.DrawState()
     
    def Quit(self) :
        pygame.display.quit()
        self._running = False

robotJoystick = LocalJoystick()
robotJoystick.main()