#!/usr/bin/env python3

# Import python modules
import sys
import os
import traceback

# Import path tool
from core import path

# Append lib path
sys.path.append(path.main()+"core/lib")

# Set pywikibot config path
os.environ["PYWIKIBOT2_DIR"] = path.main()

# Import core modules
from core.task_handler import TaskHandler
from core import log

print("äöäö")

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
