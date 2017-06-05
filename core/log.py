import datetime
from core import config
from core import colors
from core import path
import sys

time = datetime.datetime.now()
logfilename = str(time)
if config.enable_log == True:
	logfile = open(path.main()+"logs/"+logfilename+".log", "a")

def printlog(*message, end='\n'):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	time = datetime.datetime.now()
	line = str(time)+' '+finalmessage+end
	if config.enable_log == True:
		logfile.flush()
		logfile.write(line)
	sys.stdout.write(line)

def log(*message, end='\n'):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	if config.enable_log == True:
		time = datetime.datetime.now()
		line = str(time)+' '+finalmessage+end
		logfile.flush()
		logfile.write(line)

warnings = []

def warning(*message):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "
	warnings.append(finalmessage)

def printwarnings():
	global warnings
	for war in warnings:
		sys.stdout.write(colors.red+"warning: "+war+colors.end+"\n")
		log(war)
	warnings = []

def debug(*message, end='\n'):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	sys.stdout.write(finalmessage+end)
	log(finalmessage)

def crashreport(*message):
	crashfile = open(path.main()+"logs/crashreport.log", "a")
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "
	time = datetime.datetime.now()
	line = str(time)+' '+finalmessage+"\n"
	crashfile.flush()
	crashfile.write(line)
