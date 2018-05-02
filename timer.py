import time

class timer:
	#initializing
	def __init__(self, timeout):
		self.timeout = timeout
		self.current_time = time.time()
		self.stop_time = self.current_time + self.timeout


	#starting timer
	def start_timer (self):
		self.current_time = time.time()
		self.stop_time = self.current_time + self.timeout

	#time out
	def timer_timeout(self):
		if self.current_time >= self.stop_time:
			return True
		else:
			return False
