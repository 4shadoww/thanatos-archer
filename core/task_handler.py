# Python modules
from time import sleep
import traceback

# Core modules
from core import config
from core import task_loader
from core import etc
from core.log import *

class TaskHandler:
	tasks = []

	def __init__(self):
		# Load tasks
		self.tasks = task_loader.load_tasks()

	def main(self):
		# Loop
		while True:
			for task in self.tasks:
				try:
					if etc.check_time(task):
						printlog("executing task:",task.name)
						task.run()
				except:
					error = traceback.format_exc()
					printlog("unknown error:\n"+error)

			print("sleeping for", config.sleep_time, "seconds")
			sleep(config.sleep_time)