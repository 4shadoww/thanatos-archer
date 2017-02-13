from core.lop import *

class Warning:
	wm = {
	"fi": "väärä osio järjestys",}

	error_count = 0

	def __init__(self):
		self.error_count = 0

	def run(self, text):
		titles = [
		getword("seealso"),
		getword("srcs"),
		getword("refs"),
		getword("li"),
		getword("exl")]

		after = 0
		before = 1
		while True:
			if after > len(titles)-2:
				break
			if before > len(titles)-1:
				break

			if titlein(titles[after], text) == False:
				after += 1
				if after == before:
					before += 1
				continue
			elif titlein(titles[before], text) == False:
				before += 1
				continue
			if titlebefore(titles[after], titles[before], text) == False:
				self.error_count += 1
				break
			after += 1
			before += 1

		return self.error_count