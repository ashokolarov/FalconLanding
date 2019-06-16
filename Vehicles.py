import pygame
import numpy as np
from Constants import *
from PID import PID


class Rocket:
    """
    Rocket class holds data and methods used to simulate and display the rocket's dynamics

    Attributes:
        float r: rocket's radius
        float h: rocket's height
        float m_dry: dry mass of rocket
        float m_fuel: mass of fuel in the rocket
        float m_nitrogen: mass of nitrogen used by the cold gas thrusters
        float thrust_main: thrust of main engine in kN
        float engineIsp: specific impulse of main engine
        float thrust_coldgas: thrust of cold gas thruster in kN
        float mdot_coldgas: mass flow of the cold gass thruster
        float arm: distance between rcs and center of gravity of the rocket, used to calculate the moment created by rcs
        float self.throttle: throttle level of main engine
        list vel: holds rocket's x and y velocity
        float theta: rocket's orientation where counter-clockwise is positive [in deg]
        float omega: rotational speed of rocket
        pygame.Surface retracted: bitmap of rocket with retracted landing legs
        pygame.Surface extended: bitmap of rocket with extended landing legs
        pygame.Surface retracted_plumes: bitmap of rocket with retracted landing legs and main engine on
        pygame.Surface extended: bitmap of rocket with extended landing legs and main engine on
        boolean extended_bool: indicates whether rocket's landing legs are deployed
        pygame.Surface current: bitmap of the current image of the rocket
        pygame.Rectangle rect: rectangle object of the current surface used to rotate it
        int pixel_width: width of the current image in pixels
        int pixel_height: height of the current image in pixels
        list pos: holds rocket's x and y coordinates
        float altitude: distance between the bottom of the rocket and the bottom of the screen
        bool autonomous: used to indicate whether the rocket is autonomous or user-controlled
        PID PID: PID object used to calculate the necessary throttle level to land the rocket when in an autonomous regime
        bool begin_landing: used to indiicate whether landing burn has begun
        list crashed: used to indicate whether the rocket has crashed(first element) and the reason behind the crash(second element)
        bool landed: used to indicate whether the rocket has landed
        int time_taken: time taken to land the rocket
        pygame.mixer.Sound engine_sound: sound produced by the rocket's main engine

    Methods:
        property mass: calculate the current total mass of the rocket
        property moment_of_inertia: calculate the current moment of inertia
        property mdot_engine: calculate the current mass flow of the engine depending on the thrust level
        property speed: calculate the current speed of the rocket
        static to_rad: convert from degrees to radians
        static to_deg: convert from radians to degrees
        thrust_deltaV: calculate the change in velocity in the x and y axis and update the amount of fuel
        gravity_deltaV: calculate the change in velocity due to the gravitational force
        drag: calculate the change in rotational speed and velocity in the y axis due to drag
        deltaOmega: calculate the change in rotational speed due to the rcs thrusters and update the amount of nitrogen
        update_theta: calculate the resulting change in orientation due to all changes in rotational speeds
        update_pos: calculate the change in position due to all changes in velocities
        property suicide_burn: calculate the altitude at which the rocket must start burning in order to land with exactly 0 velocity
        update_pixels: update the pixel width and height depending on the current Surface
        update: apply all changes in orientation and position
        __str__: print a readable representation of the rocket


    """

    def __init__(self, radius, height, m_dry, m_fuel, m_nitrogen, thrust_main, engineIsp, thrust_coldgas, coldgasIsp,
                 Vx, Vy, X, omega, altitude, autonomous):
        """
        Object constructor

        Parameters:
            float radius: rocket's radius
            float height: rocket's height
            float m_dry: dry mass of rocket
            float m_fuel: mass of fuel in the rocket
            float m_nitrogen: mass of nitrogen used by the cold gas thrusters
            float thrust_main: thrust of main engine in kN
            float engineIsp: main engine's specific impulse
            float thrust_coldgas: thrust of cold gas thruster in kN
            float coldgasIsp: specific impulse of the rcs thrusters
            float Vx: initial velocity in the x direction
            float Vy: inital velocity in the y direction
            float X: initial x coordinate
            float omega: initial rotational speed
            float altitude: distance between the bottom of the rocket and the bottom of the screen

        """
        self.r = radius
        self.h = height
        self.m_dry = m_dry
        self.m_fuel = m_fuel
        self.m_nitrogen = m_nitrogen
        self.thrust_main = thrust_main
        self.engineIsp = engineIsp
        self.thrust_coldgss = thrust_coldgas
        self.mdot_coldgas = thrust_coldgas / (coldgasIsp * g)
        self.arm = 24
        self.throttle = 0
        self.vel = [Vx, Vy]
        self.theta = 0
        self.omega = omega
        self.retracted = pygame.image.load("images/Retracted.png")
        self.extended = pygame.image.load("images/Extended.png")
        self.retracted_plumes = pygame.image.load("images/Retracted_plumes.png")
        self.extended_plumes = pygame.image.load("images/Extended_plumes.png")
        self.extended_bool = False
        self.current = self.retracted.copy()
        self.rect = self.current.get_rect()
        self.pixel_width = self.retracted.get_width()
        self.pixel_height = self.retracted.get_height()
        self.pos = [X, 0]
        self.altitude = altitude
        self.autonomous = autonomous
        self.PID = PID(0.0045, 0.00095, 0.037, 0, 1)
        self.begin_landing = False
        self.crashed = [False, '']
        self.landed = False
        self.time_taken = 0
        self.engine_sound = pygame.mixer.Sound('sounds/rocket_engine.wav')

    @property
    def mass(self):
        """
        Calculates current total mass of rocket (dry + fuel + nitrogen)

        Returns:
            float: total mass
        """
        return self.m_fuel + self.m_dry + self.m_nitrogen

    @property
    def moment_of_inertia(self):
        """
        Calculate the current moment of inertia, assuming that the rocket is a solid cylinder
        of radius r, height h and mass m

        I = (1/12) * m * (3*r^3 + h^2)

        Returns:
             float: moment of inertia
        """
        return (1 / 12) * self.mass * ((3 * self.r ** 3) + self.h ** 2)

    @property
    def mdot_engine(self):
        """
        calculates the current mass flow of the engine depending on the thrust level

        Returns:
            float: mass flow of the main engine
        """
        return (self.thrust_main * self.throttle) / (self.engineIsp * g)

    @property
    def speed(self):
        """
        proprty method used to calculate the current speed of the rocket

        Returns:
            float: rocket's speed
        """
        return (self.vel[0]**2 + self.vel[1]**2)**0.5

    @staticmethod
    def to_rad(theta):
        """
        static method used to convert from degrees to radians

        Parameters:
            float theta: angle in degrees

        Returns:
            float: angles in radians
        """
        return (theta * np.pi) / 180

    @staticmethod
    def to_deg(theta):
        """
        static method used to convert from radians to degrees

        Parameters:
            float theta: angle in radians

        Returns:
            float: angles in degrees
        """
        return (theta * 180) / np.pi

    def thrust_deltaV(self, dt):
        """
        Apply main engine impulse to rocket, subtract the burnt fuel from the fuel mass and update the velocity vector.
        If fuel mass is less than 0, it disables the main engine.

        Parameters:
            float dt: time in seconds for which the burn occurs
        """

        if self.m_fuel <= 0:
            return 0
        a = self.thrust_main * self.throttle / self.mass
        theta = self.to_rad(self.theta)

        self.vel[0] -= a * np.sin(theta) * dt
        self.vel[1] -= a * np.cos(theta) * dt
        self.m_fuel -= self.mdot_engine * dt

    def gravity_deltaV(self, dt):
        """
        Add the velocity change due to the gravity to the velocity vector

         Parameters:
             float dt: time in seconds for which the rocket is affected by gravity
        """

        self.vel[1] += g * dt

    def drag(self, dt):
        """
        1. Computes the aerodynamic moment created due to the rotation of the rocket and applies it to decrease
        the rotational speed

        2. Computes the drag and the corresponding change in velocity in the y directions

        Parameters:
            float dt: time for which the rocket is affected by the drag in seconds
        """

        M = (1/12) * Cd * rho * np.pi * (self.omega ** 2) * self.r * (self.h/2)**4
        if self.omega < 0:
            self.omega += self.to_deg((M / self.moment_of_inertia) * dt)
        else:
            self.omega -= self.to_deg((M / self.moment_of_inertia) * dt)

        D = 0.5 * Cd * rho * (self.speed ** 2) * (np.pi * self.r**2)
        self.vel[1] -= (D / self.mass) * dt

    def deltaOmega(self, dt, thruster):
        """
        1. Calculate the change in angular velocity due to the cold gas thruster
        If the left thruster is used, the rotation produced is clockwise (-)
        If the right thruster is used, the rotation produced is counter-clockwise (+)

        2. Updates the nitrogen mass after the thruster is used and if it is less than 0, disables the rcs system

        Parameters:
             float dt: time in seconds for which the cold gas thruster is used
             string thruster: parameter used to indicated whether the left or right rcs thruster is used
        """
        if self.m_nitrogen <= 0:
            return 0
        if thruster == 'LEFT':
            self.omega -= (self.thrust_coldgss * self.arm * dt) / self.moment_of_inertia
        elif thruster == 'RIGHT':
            self.omega += (self.thrust_coldgss * self.arm * dt) / self.moment_of_inertia
        self.m_nitrogen -= self.mdot_coldgas * dt

    def update_theta(self, dt):
        """
        calculate the change in orientation due to all moments applied.

        Parameters:
            float dt: time in seconds for which the moments are applied
        """
        self.theta += self.to_deg(self.omega) * dt

    def update_pos(self, dt):
        """
        calculate the change in position due to all changes in velocities

        Parameters:
            float dt: time in seconds for which accelerations are applied
        """
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt

    @property
    def suicide_burn(self):
        """
        property method used to calculate the altitude at which the rocket must start burning in order to reach 0 velocity just above the barge

        Returns:
             float: suicide burn altitude
        """
        return (self.vel[1] ** 2)/(2 * ((self.thrust_main / self.mass) - g))

    def update_pixels(self):
        """
        update the pixel width and height depending on the current Surface
        """
        self.pixel_height = self.current.get_height()
        self.pixel_width = self.current.get_width()

    def update(self, dt, thruster):
        """
        1. Apply all updates in position and orientation of the rocket.
        2. Calculate the new center of the pygame.Rectangle object used to represent the rocket after any rotations
        3. Change the current surface of the rocket if the main engine is ignited or the landing legs are deployed

        Parameters:
            float dt: time for which all forces and moments are applied
            string thruster: used to indicated whether the left or right rcs thruster is used

        """
        self.thrust_deltaV(dt)
        self.gravity_deltaV(dt)
        self.drag(dt)
        if isinstance(thruster, str):
            self.deltaOmega(dt, thruster)
        self.update_theta(dt)
        if not self.extended_bool:
            if self.throttle > 0 and self.m_fuel > 0:
                self.current = pygame.transform.rotate(self.retracted_plumes, self.theta)
            else:
                self.current = pygame.transform.rotate(self.retracted, self.theta)
                self.engine_sound.stop()
        else:
            if self.throttle > 0 and self.m_fuel > 0:
                self.current = pygame.transform.rotate(self.extended_plumes, self.theta)
            else:
                self.current = pygame.transform.rotate(self.extended, self.theta)
                self.engine_sound.stop()
        self.update_pixels()
        self.rect = self.current.get_rect(center=self.pos)
        self.update_pos(dt)

    def __str__(self):
        """
        Dunder method to print a user-friendly string of text describing the rocket's physical parameters

        Returns:
            string: Rocket's main engine thruster, rcs thrust, mass, moment of inertia, radius, height
        """
        return f'''\t\tFalcon 9 booster\n
        Thrust of main engine: {self.thrust_main}N\n
        Thrust of rcs thruster: {self.thrust_coldgss}N\n
        Mass: {self.mass}kg\n 
        Moment of inertia: {self.moment_of_inertia}kgm^2\n
        Radius: {self.r}m\n
        Height: {self.h}m\n
        '''


class Barge:
    """
    Barge class holds data and methods used to simulate and display the barge

    Attributes:
        int width: width of barge in pixels
        int height: height of barge in pixels
        int pos: x coordinate of the barge
        int vel: x velocity of the barge

    Methods:
        update: update the position of the barge depending on the velocity
    """

    def __init__(self, width, height, pos, vel):
        """
        Constructor

        Parameters:
             int width: width of barge in pixels
            int height: height of barge in pixels
            int pos: x coordinate of the barge
            int vel: x velocity of the barge

        """
        self.width = width
        self.height = height
        self.pos = pos
        self.vel = vel

    def update(self, dt):
        """
        update the position of the barge depending on the velocity

        Parameters:
            float dt: time in seconds for which the barge moves
        """
        self.pos += self.vel * dt
