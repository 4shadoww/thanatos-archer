# Execute time checker
# Import python modules
import datetime

from tinydb import TinyDB, Query

# Import core modules
from core.log import *

# Init db
db = TinyDB("core/db/etdb.json")

def check(task, time):
	exet = Query()

	matches = db.search(exet.name == task.name)

	if matches == []:
		db.insert({"name": task.name, "time": datetime.datetime.now().strftime("%m%d%H%M%S")})

	else:
		lastexecute = matches[0]["time"]

	tasktime = time.split("/")

	if tasktime[0] == "*" and tasktime[1] == "*" and tasktime[2] == "*" and tasktime[3] == "*":
		db.update({"time": datetime.datetime.now().strftime("%m%d%H%M%S")}, exet.name == task.name)
		return True

	timenow = datetime.datetime.now().strftime("%m%d%H%M")
	final_tn = datetime.datetime.now().strftime("%m%d%M%H")
	final_le = lastexecute[:len(lastexecute)-2]
	final_tt = ""
	resolution = 0
	nums = False
	for i in reversed(tasktime):
		if i == "*":
			if nums == True:
				final_tt += "00"
			else:
				final_tt += "**"
		else:
			nums = True
			if len(i) == 1:
				final_tt += "0"+i
			else:
				final_tt += i

	for i in final_tt:
		if i == "*":
			resolution += 1

	if int(timenow[resolution:]) > int(lastexecute[resolution:]) and int(timenow[resolution:]) > int(final_tn[resolution:]):
		db.update({"time": datetime.datetime.now().strftime("%m%d%H%M%S")}, exet.name == task.name)
		return True

	return False

def check_time(task):
	for time in task.time:
		if check(task, time):
			return True

	return False
