import re
from core import config
from core.langdict import *
from core.log import *

warnings = {
	"war0fi": "lop ristiriita: kaksi samanlaista riviä",
}

def andop(items, text):
	for item in items:
		if item in text:
			return True
	return False

def istag(tag, data):
	if data.count("<") == 1 and data.count(">") == 1 and tag in data:
		data = re.sub('[^a-zA-Z0-9 ]', ' ', data).split()

		if data[0] == tag:
			return True
	return False


def getword(id, lang=None):
	if lang == None:
		wl = globals()[config.lang]
		return wl[id]
	
	wl = globals()[lang]
	return wl[id]

def getwordlc(id, lang=None):
	if lang == None:
		wl = globals()[config.lang]
		return wl[id].lower()
	
	wl = globals()[lang]
	return wl[id].lower()

def getwordlcc(id, lang=None):
	if lang == None:
		wl = globals()[config.lang]
		return wl[id].lower()+":"
	
	wl = globals()[lang]
	return wl[id].lower()+":"

def getwordulc(id, lang=None):
	if lang == None:
		wl = globals()[config.lang]
		return wl[id], wl[id].lower()
	
	wl = globals()[lang]
	return wl[id], wl[id].lower()

def getwordc(id, lang=None):
	if lang == None:
		wl = globals()[config.lang]
		return wl[id]+":"
	
	wl = globals()[lang]
	return wl[id]+":"

def titlein(title, text):
	titles = re.findall(r"\=.*\=", text)
	for i in titles:
		if re.sub('[^a-zA-Z0-9åäöÅÄÖ]', '', i) == re.sub('[^a-zA-Z0-9åäöÅÄÖ]', '', title):
			return True

	return False

def titlepos(title, text):
	titles = re.findall(r"\=.*\=", text)
	for i in titles:
		if re.sub('[^a-zA-Z0-9åäöÅÄÖ]', '', i) == re.sub('[^a-zA-Z0-9åäöÅÄÖ]', '', title):
			return text.find(i)

	return False

def titleline(title, text):
	for l, line in enumerate(text.split("\n")):
		titles = re.findall(r"\=.*\=", line)
		for item in titles:
			if re.sub('[^a-zA-Z0-9åäöÅÄÖ]', '', item) == re.sub('[^a-zA-Z0-9åäöÅÄÖ]', '', title):
				return l

	return False

def zeromatch(items, text):
	for item in items:
		if item in text:
			return False

	return True

def anymatch(items, text):
	for item in items:
		if item in text:
			return True

	return False

def abandop(items, match):
	for item in items:
		if item == match:
			return True
	return False

def istitle(title):
	titles = re.findall(r"\=.*\=", title)

	if len(titles) > 0 and re.sub('[^a-zA-Z0-9åäöÅÄÖ]', '', titles[0]) == re.sub('[^a-zA-Z0-9åäöÅÄÖ]', '', title):
		return True

	return False

def titlebefore(after, before, text, subtitles=True):
	text = text.split("\n")
	nextref = False

	for line in text:
		if titlein(after, line):
			nextref = True
			continue
		if titlein(before, line) and nextref:
			return True
		elif istitle(line) and nextref:
			if subtitles == False and "===" not in line:
				return False
			elif subtitles == True:
				return False
	return False

def listend(text, title, listitems, nono, spaces):
	startpos = titleline(title, text)
	endpos = titleline(title, text)
	text = text.split("\n")
	belows = text[startpos:len(text)-1]
	tries = 0
	lasttemp = 0
	listfound = False
	lastvalid = None

	for l in  range(0, len(belows)):
		if l == 0:
			continue

		if anymatch(listitems, belows[l]):
			listfound = True
			lastvalid = len(text)-len(belows)+l

		if belows[l] == "":
			tries += 1
			lastvalid = len(text)-len(belows)+l-1
		else:
			tries = 0

		if l == 3 and listfound == False:
			endpos = len(text)-len(belows)
			break

		if tries >= 2:
			endpos = len(text)-len(belows)+l
			break

		if istitle(belows[l]) and "===" not in belows[l]:
			endpos = len(text)-len(belows)+l-2
			break

		if anymatch(listitems, belows[l]) and "{{" in belows[l] and anymatch(nono, belows[l]) == False:
			lasttemp += belows[l].count("{{")

		if "}}" in belows[l] and lasttemp > 0:
			lasttemp -= belows[l].count("}}")
			continue

		if anymatch(nono, belows[l]):
			endpos = len(text)-len(belows)+l-2
			break

		if zeromatch(listitems, belows[l]) and listfound and l+1 != len(belows) and zeromatch(listitems, belows[l+1]):
			endpos = len(text)-len(belows)+l-2
			break

		if l == len(belows)-1 and lastvalid != None:
			endpos = lastvalid

	return startpos, endpos, listfound

def removefromlist(sec, listobj):
	confirmed = False
	i = 0
	startpos = None

	for l in range(0, len(listobj)):
		if i == len(sec):
			confirmed = True
			break

		if sec[i] == listobj[l]:
			if startpos == None:
				startpos = l
			i += 1
		else:
			startpos = None
			i = 0	

	for l in range(0, len(sec)):
		listobj.pop(startpos)

	return listobj