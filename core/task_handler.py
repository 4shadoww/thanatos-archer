# Python modules
from time import sleep
import traceback
import datetime

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
		oldtimenow = None
		while True:
			printsleep = True
			timenow = datetime.datetime.now()
			if not oldtimenow:
				oldtimenow = timenow
			for task in self.tasks:
				try:
					if etc.check_time(task, timenow, oldtimenow):
						printlog("executing task:",task.name)
						task.run()
						printsleep = True
				except:
					error = traceback.format_exc()
					printlog("unknown error:\n"+error)

			after_run = datetime.datetime.now()
			oldtimenow = timenow
			sleeptime = config.sleep_time
			if sleeptime > 59:
				sleeptime = 59
			if after_run - timenow < datetime.timedelta(seconds=sleeptime):
				if printsleep:
					printlog("now sleeping...")
				sleep(config.sleep_time)
