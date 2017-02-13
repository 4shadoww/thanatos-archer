from core.lop import *

class Warning:
	wm = {
	"fi": "Viitteet osio on Lähteet osion yläpuolella",}

	error_count = 0

	def __init__(self):
		self.error_count = 0

	def run(self, text):
		if titlein(getword("srcs"),text) and titlein(getword("refs"), text) and titleline(getword("srcs"), text) > titleline(getword("refs"), text):
			self.error_count += 1
		return self.error_count