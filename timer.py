import time

class timer(object):

    TIMER_STOP = 0

    #initializing
    def __init__(self,timeout):
        self.start_time = self .TIMER_STOP
        self.TIME_OUT = timeout

     #starting timer
    def start_timer (self):
        if self.start_time == self .TIMER_STOP:
            self.start_time = time.time()

    #Stopping timer
    def stop_timer (self):
        if self.start_time != self.TIMER_STOP:
            self.start_time = self.TIMER_STOP

    #time out
    def timer_timeout (self):
        if not self.timer_running():
            return False
        else:
            if ((time.time() - self.start_time) >= self.TIME_OUT) :
                return True