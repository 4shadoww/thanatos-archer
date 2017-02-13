from core.lop import *

class Warning:
	wm = {
	"fi": "artikkelissa on viitteet osio tai malline, mutta ei yhtään <ref> tagia",}

	error_count = 0

	def __init__(self):
		self.error_count = 0

	def run(self, text):
		if titlein(getword("refs"), text) and "<ref" not in text:
			self.error_count += 1

		if "{{"+getword("refs") in text and "<ref" not in text or "{{"+getwordlc("refs") in text and "<ref" not in text:
			self.error_count += 1

		return self.error_count