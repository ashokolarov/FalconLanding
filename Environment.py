import pygame
from Constants import *
from Vehicles import Rocket, Barge
import sys
from random import uniform


class Environment:
    """
    Environment class used to start the game, receive user input and display all objects.

    Attributes:
        int width: display width
        int height: display height
        pygame.font.SysFont font: font used to display text in pygame
        pygame.font.SysFont font_big: font used to display bigger text in pygame
        pygame.Surface win: display object in which the game runs
        list startScreens: a list used to store the three starting screen images
        list rockets: a list used to store all rocket objects used in the simulation
        list barges: a list used to store all barge objects used in the simulation
        float water_height: the height used to draw the water in the display
        string rocket_thruster: used to indicate which rcs thruster(Left/Right) is used
        float dt: time between updates
        bool running: boolean used to indicate whether the game is still running
        pygame.time.Clock(): clock object used to keep track of the time for which the simulation has been running
        float time: time for which the simulation has been running

    Methods:
        update_keys: check if any keys have been pressed by the user
        collision_detect: check if the rocket has collided with any of the objects within the display or gotten out of bounds
        print_info: display information about the rocket
        update: step through the simulation and update all objects
        play: run the simulation until the rockets have landed or crashed


    """

    def __init__(self, width, height):
        """
        Object constructor used to initialize the pygame window, iterate over the starting screens and get user input
        to decide which game mode to run

        Parameters:
            int width: window width
            int height: window height

        Rocket parameters:
            radius: 1.85m
            height: 44m
            dry mass: 27200kg
            fuel mass: 1900kg
            nitrogen mass: 500kg
            thrust of main engine: 845 000N
            specific impulse of main engine: 296.5s
            thrust of rcs thrusters: 25 000N
            specific impulse of rcs thrusters: 60s
        """
        pygame.init()
        pygame.font.init()

        self.width = width
        self.height = height
        self.font = pygame.font.SysFont('Comic Sans MS', 20)
        self.font_big = pygame.font.SysFont('Comic Sans MS', 50)

        self.win = pygame.display.set_mode((width, height))
        self.startScreens = [pygame.image.load("images/StartScreen1.jpg"), pygame.image.load("images/StartScreen2.jpg"),
                             pygame.image.load("images/StartScreen3.jpg")]
        pygame.display.set_caption('Falcon Landing')

        self.win.blit(self.startScreens[0], (0, 0))
        pygame.display.update()

        start = False
        screen = 0
        while not start:
            events = pygame.event.get()
            for event in events:

                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        screen -= 1

                    if event.key == pygame.K_DOWN:
                        screen += 1

                    if event.key == pygame.K_RETURN:
                        start = True

                    if screen > 2:
                        screen = 0

                    if screen < 0:
                        screen = 0

            self.win.blit(self.startScreens[screen], (0, 0))
            pygame.display.update()

        pygame.time.delay(500)

        # initialize rocket with a random angular speed
        omega = uniform(-2, 2)

        # all rockets get initialized with a vertical velocity of 100m/s
        if screen == 0:
            self.win = pygame.display.set_mode((900, height))
            self.rockets = [Rocket(1.85, 44, 27200, 1900, 500, 845e3, 296.5, 25e3, 60, 0, 100,
                                   400, omega, height, False)]
            self.barges = [Barge(100, 5, 350, 0)]

        elif screen == 1:
            self.win = pygame.display.set_mode((900, height))
            self.rockets = [Rocket(1.85, 44, 27200, 1900, 500, 845e3, 296.5, 25e3, 60, 0, 100,
                                   400, omega, height, True)]
            self.barges = [Barge(100, 5, 350, 0)]

        elif screen == 2:
            user = Rocket(1.85, 44, 27200, 1900, 500, 845e3, 296.5, 25e3, 60, 0, 100, 400, omega,
                          height, False)
            computer = Rocket(1.85, 44, 27200, 1900, 500, 845e3, 296.5, 25e3, 60, 0, 100, 1200,
                              omega, height, True)
            self.rockets = [user, computer]
            barge1 = Barge(100, 5, 350, 0)
            barge2 = Barge(100, 5, 1150, 0)
            self.barges = [barge1, barge2]

        self.water_height = 0.015 * height
        self.rocket_thruster = None

        self.dt = 0.04
        self.running = True
        self.clock = pygame.time.Clock()
        self.time = 0
        self.play()

    def update_keys(self):
        """
        method used to get the keys pressed by the user and apply control to the rocket depending on them

        """
        keys = pygame.key.get_pressed()

        self.rocket_thruster = None

        # Full throttle, start engine sound
        if keys[pygame.K_z]:
            self.rockets[0].throttle = 1
            self.rockets[0].engine_sound.play()
            self.rockets[0].engine_sound.set_volume(0.3)

        # Zero throttle, stop engine sound
        elif keys[pygame.K_x]:
            self.rockets[0].throttle = 0
            pygame.mixer.stop()

        # Decrease throttle level by 0.01
        elif keys[pygame.K_LCTRL]:
            self.rockets[0].throttle -= 0.01
            if self.rockets[0].throttle <= 0:
                self.rockets[0].throttle = 0

        # Increase throttle level by 0.01
        elif keys[pygame.K_LSHIFT]:
            self.rockets[0].throttle += 0.01
            if self.rockets[0].throttle >= 1:
                self.rockets[0].throttle = 1

        # Use left rcs thruster
        elif keys[pygame.K_RIGHT]:
            self.rocket_thruster = 'LEFT'

        # Use right rcs thruster
        elif keys[pygame.K_LEFT]:
            self.rocket_thruster = 'RIGHT'

        # Extend landing legs
        elif keys[pygame.K_g]:
            self.rockets[0].extended_bool = True

        # Set the volume depending on the throttle level
        if self.rockets[0].throttle > 0.3:
            self.rockets[0].engine_sound.set_volume(0.3)
        else:
            self.rockets[0].engine_sound.set_volume(self.rockets[0].throttle)

    def collision_detect(self, rocket, barge):
        """
        method used to detect any collision that have taken place between the objects in the game

        Parameters:
            Rocket rocket: rocket object used in the game
            Barge barge: barge object used in the simulation
        """

        # If the rocket gets out of the screen, stop the game
        if rocket.pos[0] < 0 or rocket.pos[0] + rocket.pixel_width > self.width:
            rocket.crashed[0] = True
            rocket.crashed[1] = 'Loss of Communication'

        # If the rocket gets out of the screen, stop the game
        if rocket.pos[1] < 0 or (rocket.pos[1] + rocket.pixel_height / 2) > self.height:
            rocket.crashed[0] = True
            rocket.crashed[1] = 'Loss of Communication'

        # If the orientation is bigger than 90 degrees, destroy the rocket
        if abs(rocket.theta) > 90:
            rocket.crashed[0] = True
            rocket.crashed[1] = 'Destroyed by aerodynamic forces'

        # Collision with barge
        if (rocket.pos[0] > barge.pos) and ((rocket.pos[0] + rocket.pixel_width) < (barge.pos + barge.width)):
            if (rocket.pos[1] + rocket.pixel_height / 2) >= (self.height - barge.height - self.water_height):
                # if the velocity is too high, consider it a crash
                if abs(rocket.vel[0]) > 15 or rocket.vel[1] > 15:
                    rocket.crashed[0] = True
                    rocket.crashed[1] = 'Crashed into barge'
                else:
                    # otherwise, cut the engine off and apply momentum exchange
                    rocket.thrust_main = 0
                    rocket.vel[0] *= -e
                    rocket.vel[0] += barge.vel
                    rocket.vel[1] *= -e
                    rocket.engine_sound.stop()
                    rocket.landed = True

                    # record the time taken to land the rocket
                    if rocket.time_taken == 0:
                        rocket.time_taken = self.time

                # if the landing legs are not deployed, consider it a crash
                if not rocket.extended_bool:
                    rocket.crashed[0] = True
                    rocket.crashed[1] = 'Landing legs not deployed'
        else:
            # if the rocket is not withing the boundaries of the barge, then it has crashed into the ocean
            if (rocket.pos[1] + rocket.pixel_height / 2) > (self.height - self.water_height):
                rocket.crashed[0] = True
                rocket.crashed[1] = 'Crashed into ocean'

    def print_info(self, rocket, x, y):
        """
        Print all relevant information about the rocket to the screen and update the time

        Parameters:
             Rocket rocket: the rocket object whose information needs to be displayed
             int x, y: starting coordinates of the first message to be displayed
        """
        info1 = self.font.render(f'Vx: {rocket.vel[0]:.0f}, Vy: {rocket.vel[1]:.0f}', True, (0, 0, 0))
        info2 = self.font.render(f'Omega: {rocket.omega:.2f}', True, (0, 0, 0))
        info3 = self.font.render(f'Fuel: {rocket.m_fuel:.0f}', True, (0, 0, 0))
        info4 = self.font.render(f'Cold gas: {rocket.m_nitrogen:.0f}', True, (0, 0, 0))
        info5 = self.font.render(f'Altitude: {self.height - rocket.pos[1]:.0f}', True, (0, 0, 0))
        info6 = self.font.render(f'Throttle: {rocket.throttle:.2f}', True, (0, 0, 0))

        self.win.blit(info1, (x, y))
        self.win.blit(info2, (x, y+20))
        self.win.blit(info3, (x, y+600))
        self.win.blit(info4, (x, y+650))
        self.win.blit(info5, (x, y+40))
        self.win.blit(info6, (x, y+60))

        self.time += self.clock.tick()

    def update(self):
        """
        Step through the simulation and display all objects
        """
        self.win.fill(BLUE)

        for i in range(len(self.rockets)):
            # Print message if the rocket has crashed
            if self.rockets[i].crashed[0]:
                message = self.font_big.render(f'{self.rockets[i].crashed[1]}!', True, (0, 0, 0))
                if i == 0:
                    self.win.blit(message, (200, self.height / 2))
                else:
                    self.win.blit(message, (1200, self.height / 2))

            else:
                # if the rocket is autonomous, run through the PID loop and compute the new throttle value
                if self.rockets[i].autonomous:
                    if (self.rockets[i].suicide_burn > (self.height - self.rockets[i].pos[1])) or self.rockets[i].begin_landing:
                        self.rockets[i].begin_landing = True

                        P = self.rockets[i].vel[1]
                        I = self.height - self.rockets[i].pos[1]
                        D = (self.rockets[i].thrust_main / self.rockets[i].mass) - g

                        self.rockets[i].throttle = self.rockets[i].PID.control(P, I, D)
                        if self.rockets[i].throttle > 0:
                            self.rockets[i].engine_sound.play()
                            self.rockets[i].engine_sound.set_volume(0.3)

                    # Extend landing legs when 100m above the barge
                    if (self.height - self.rockets[i].pos[1]) < (self.water_height + self.barges[i].height + 100):
                        self.rockets[i].extended_bool = True

                    # If the rocket is rotating, apply rcs to stabilize it and return back to an angle of 0 degrees
                    if self.rockets[i].theta < 0:
                        self.rockets[i].update(self.dt, 'RIGHT')
                    elif self.rockets[i].theta > 0:
                        self.rockets[i].update(self.dt, 'LEFT')
                    else:
                        self.rockets[i].update(self.dt, None)
                else:
                    # if the rocket is not autonomous, get user input
                    self.update_keys()
                    self.rockets[i].update(self.dt, self.rocket_thruster)

                # check for collision and update the position of the barge
                self.collision_detect(self.rockets[i], self.barges[i])
                self.barges[i].update(self.dt)

            # Draw the ocean and the sky
            pygame.draw.rect(self.win, GRAY, [self.barges[i].pos, (self.height - self.water_height - self.barges[i].height), self.barges[i].width, self.barges[i].height])
            pygame.draw.rect(self.win, DARK_BLUE, [0, self.height - self.water_height, self.width, self.water_height])

            # Print rocket info on the screen
            self.win.blit(self.rockets[i].current, self.rockets[i].rect)
            if i == 0:
                self.print_info(self.rockets[i], 10, 10)
            else:
                self.print_info(self.rockets[i], 1500, 10)

            self.time += self.clock.tick()

    def play(self):
        """
        Start the game

        """
        while self.running:
            # while the game is still running, update the objects in it
            self.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    global play_again
                    play_again = False

            #get keys pressed and do something depending on them
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.running = False
                play_again = False

            #check if the rockets have landed or crashed and print the time taken 
            if len(self.rockets) == 1:
                if self.rockets[0].landed or self.rockets[0].crashed[0]:
                    pygame.mixer.stop()
                    if self.rockets[0].landed:
                        time_info = self.font.render(f'Time taken: {self.rockets[0].time_taken}', True, (0, 0, 0))
                        self.win.blit(time_info, (0, self.height - 40))
                    info = self.font_big.render('If you want to play again, press ENTER', True, (0, 0, 0))
                    self.win.blit(info, (self.width / 10, self.height / 3))
                    if keys[pygame.K_RETURN]:
                        self.running = False

            elif len(self.rockets) == 2:
                if (self.rockets[0].landed or self.rockets[0].crashed[0]) and (self.rockets[1].landed or self.rockets[1].crashed[0]):
                    pygame.mixer.stop()
                    if self.rockets[0].landed:
                        time_info = self.font.render(f'Time taken: {self.rockets[0].time_taken}', True, (0, 0, 0))
                        self.win.blit(time_info, (0, self.height - 40))
                    if self.rockets[1].landed:
                        time_info = self.font.render(f'Time taken: {self.rockets[1].time_taken}', True, (0, 0, 0))
                        self.win.blit(time_info, (self.width - 200, self.height - 40))
                    info = self.font_big.render('If you want to play again, press ENTER', True, (0, 0, 0))
                    self.win.blit(info, (self.width / 4, self.height / 3))
                    if keys[pygame.K_RETURN]:
                        self.running = False
            self.clock.tick(self.dt * 1e3)
            pygame.display.update()
        pygame.quit()


if __name__ == '__main__':
    play_again = True
    while play_again:
        env = Environment(1600, 900)
