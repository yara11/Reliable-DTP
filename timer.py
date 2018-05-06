import time

class timer:
	#initializing
	def __init__(self, timeout):
		self.timeout = timeout
		self.start_timer()


	#starting timer
	def start_timer(self):
		self.stop_time = time.time() + self.timeout

	#time out
	def timer_timeout(self):
		if time.time() >= self.stop_time:
			return True
		else:
			return False
