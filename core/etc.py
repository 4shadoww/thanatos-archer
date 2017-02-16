# Execute time checker

import datetime
# Import core modules
from core.log import *

def check(time, timenow, oldtimenow, task):

	if timenow == oldtimenow and task.exeonstart:
		return True

	tasktime = time.split("/")

	tasktimeobj = timenow

	for i, value in enumerate(tasktime):
		if i == 0 and value != "*":
			tasktimeobj = tasktimeobj.replace(minute = int(value))
		elif i == 1 and value != "*":
			tasktimeobj = tasktimeobj.replace(hour = int(value))
		elif i == 2 and value != "*":
			tasktimeobj = tasktimeobj.replace(day = int(value))
		if i == 3 and value != "*":
			tasktimeobj = tasktimeobj.replace(month = int(value))

	if tasktimeobj > oldtimenow and tasktimeobj < timenow:
		return True

	meani = 0
	meanic = 0

	for i, value in enumerate(tasktime):
		if value != "*":
			meani += 1
		if i == 0 and value != "*" and int(value) == timenow.minute:
			meanic += 1
		elif i == 1 and value != "*" and int(value) == timenow.hour:
			meanic += 1
		elif i == 2 and value != "*" and int(value) == timenow.day:
			meanic += 1
		elif i == 3 and value != "*" and int(value) == timenow.month:
			meanic += 1

	if meani == meanic:
		return True
	else:
		return False

def check_time(task, timenow, oldtimenow):
	for time in task.time:
		return check(time, timenow, oldtimenow, task)
