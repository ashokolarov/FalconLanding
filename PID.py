class PID:
    """
    PID controller class used to compute the throttle level of the rocket in order to land it.

    Attributes:
        float Kp: Proportional gain of the controller
        float Ki: Integral gain of the controller
        float Kd: Derivative gain of the controller
        float limit_low: bottom threshold of the signal
        float limit_high: top threshold of the signal

    Methods:
        control: compute the throttle level of the rocket
    """

    def __init__(self, Kp, Ki, Kd, limit_low, limit_high):
        """
        Object constructor

        Parameters:
            float Kp: Proportional gain of the controller
            float Ki: Integral gain of the controller
            float Kd: Derivative gain of the controller
            float limit_low: bottom threshold of the signal
            float limit_high: top threshold of the signal
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.limit_low = limit_low
        self.limit_high = limit_high

    def control(self, proportional, integral, derivative):
        """
        compute the throttle level of the rocket

        Parameters:
            float proportional: proportional term of the controller
            float integral: integral term of the controller
            float derivative: derivative term of the controller

        Returns:
            float signal: throttle level
        """
        signal = self.Kp * proportional + self.Ki * integral + self.Kd * derivative

        if signal > self.limit_high:
            return self.limit_high
        elif signal < self.limit_low:
            return self.limit_low
        else:
            return signal
