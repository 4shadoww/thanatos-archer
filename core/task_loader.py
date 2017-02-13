# Import python modules
import importlib

# Import core modules
from core.config import *

def load_tasks():
	objects = []

	for task in tasks:
		if task not in ignore_tasks:
			module = importlib.import_module("core.tasks."+task)
			objects.append(module.ThanatosTask())

	return objects