#!/usr/bin/env python3

# Import python modules
import sys
import os

# Append lib path
sys.path.append("core/lib")

# Import core modules
from core.task_handler import TaskHandler 

def main():
	try:
		task_handler = TaskHandler()
		task_handler.main()
	except KeyboardInterrupt:
		print("thanatos terminated")

if __name__ == "__main__":
	main()