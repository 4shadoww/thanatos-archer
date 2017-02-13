from core.lop import *

class Warning:
	wm = {
	"fi": "tukematon viitteet malline",}

	error_count = 0

	def __init__(self):
		self.error_count = 0

	def run(self, text):
		if "{{"+getword("refs")+"|" in text and "|"+getword("refs")+"=" in text:
			self.error_count += 1
		if "{{"+getword("refs")+"|" in text and "|"+getwordlc("refs")+"=" in text:
			self.error_count += 1
		if "<references>" in text:
			self.error_count += 1
		return self.error_count