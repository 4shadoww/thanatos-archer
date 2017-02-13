import importlib
from core import config
from core import colors
from core.log import *

# Import core modules
from core.config import *

# Init warning modules
waralgs = []

for war in config.warnings:
	if war not in config.ignore_war:
		module = importlib.import_module("core.warnings."+war)
		waralgs.append(module.Warning())

def check(text, article):
	warnings = False

	for warmeth in waralgs:
		warmeth.__init__()
		error_count = warmeth.run(text)
		if error_count > 0:
			warnings = True
			log("warning: "+warmeth.wm[config.lang])
			print(colors.red+"warning: "+warmeth.wm[config.lang]+colors.end)

	return warnings