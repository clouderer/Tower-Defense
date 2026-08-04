import pygame 
import math
from abc import ABC, abstractmethod


class Enemy: 
    def __init__(self, path): 
        self.max_health = 30
        self.health = self.max_health

        self.speed  = 20
        self.reward = 10

        self.path = path
        self.current_waypoint = 1

        self.x_position, self.y_position = path[0]
        self.distance_to_finish = self.calculate_distance_to_finish()

        self.is_alive = True
        self.reached_end = False

        self.height = 15

    def calculate_distance(self): 
        target_x, target_y = self.path[self.current_waypoint]
        
        dx = target_x - self.x_position
        dy = target_y - self.y_position
        
        return math.hypot(dx,dy)

    def draw_health(self, window): 
        health_red = pygame.Rect(0, 0, 20, 4)
        health_red.center = (self.x_position, self.y_position - self.height)

        health_green = pygame.Rect(0, 0, (self.health / self.max_health) * 20, 4)
        health_green.topleft = health_red.topleft

        pygame.draw.rect(window, "Red", health_red)
        pygame.draw.rect(window, "Green", health_green)
    
    #[TO DO] abstract this 
    def draw(self, window): 
        pygame.draw.circle(window, "Orange", (self.x_position, self.y_position), 10)
        self.draw_health(window)

    def update(self, dt): 
        if self.reached_end: 
            return 
    
        self.move(dt)
        self.distance_to_finish = self.calculate_distance_to_finish()

    def move(self,dt):
        target_x, target_y = self.path[self.current_waypoint]
        
        dx = target_x - self.x_position
        dy = target_y - self.y_position
        
        distance = self.calculate_distance()
        remaining_distance = dt * self.speed
        
        if remaining_distance >= distance: 
            self.x_position, self.y_position = self.path[self.current_waypoint]
            self.current_waypoint += 1
        else: 
            self.x_position += (dx / distance) * remaining_distance 
            self.y_position += (dy / distance) * remaining_distance
        
        if self.current_waypoint >= len(self.path):
            self.reached_end = True

    def calculate_distance_to_finish(self): 
        if self.current_waypoint >= len(self.path): 
            return 0

        remaining_distance = self.calculate_distance()

        for i in range(self.current_waypoint, len(self.path) - 1):
            x1,y1 = self.path[i]
            x2,y2 = self.path[i + 1]

            remaining_distance += math.hypot(x2 - x1, y2 - y1)

        return int(remaining_distance)

#__________________________________________________________________________________________

    def draw_distance(self, window): 
            font = pygame.font.Font("freesansbold.ttf", 10)
            text = font.render("P: " + str(self.distance_to_finish), True, "Purple")
            text_rect = text.get_rect(bottomright = (590,320))
            window.blit(text, text_rect)
            
        

