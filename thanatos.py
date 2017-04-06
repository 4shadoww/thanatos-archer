#!/usr/bin/env python3

# Import python modules
import sys
import os
import traceback

# Append lib path
sys.path.append("core/lib")

# Import core modules
from core.task_handler import TaskHandler
from core import log

def main():
	try:
		task_handler = TaskHandler()
		task_handler.main()
	except KeyboardInterrupt:
		print("thanatos terminated")

	except:
		traceback.print_exc()
		log.crashreport(traceback.format_exc())

if __name__ == "__main__":
	main()
