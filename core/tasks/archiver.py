from core.taskcore import *
import re
from pywikibot import textlib
import datetime
import pywikibot
from tinydb import TinyDB, Query
import traceback
import datetime

class UnsupportedConfig(Exception):
	pass

def template_title_regex(tpl_page):
	"""
	Return a regex that matches to variations of the template title.

	It supports the transcluding variant as well as localized namespaces and
	case-insensitivity depending on the namespace.

	@param tpl_page: The template page
	@type tpl_page: Page
	"""
	ns = tpl_page.site.namespaces[tpl_page.namespace()]
	marker = '?' if ns.id == 10 else ''
	title = tpl_page.title(withNamespace=False)
	if ns.case != 'case-sensitive':
		title = '[%s%s]%s' % (re.escape(title[0].upper()),
							  re.escape(title[0].lower()),
							  re.escape(title[1:]))
	else:
		title = re.escape(title)

	return re.compile(r'(?:(?:%s):)%s%s' % (u'|'.join(ns), marker, title))


class DiscussionPage:
	config = None
	text = None
	threads = None
	oldthreads = None
	toarchive = None
	name = None
	counter = None

class Config:
	archive = "Arkisto %(counter)d"
	algo = "30d"
	counter = None
	maxarchivesize = "100kt"
	minthreadsleft = 5
	minthreadstoarchive = 0
	archiveheader = "{{Arkisto}}"
	counter = None

class Thread:
	content = None
	timestamp = None
	site = None

	def __init__(self, content, ts):
		self.content = content
		self.getdate(ts)

	def getdate(self, ts):
		for line in self.content:
			linedate = ts.timestripper(line)
			if linedate:
				if not self.timestamp:
					self.timestamp = linedate
				else:
					self.timestamp = max(self.timestamp, linedate)


class TZoneUTC(datetime.tzinfo):

	"""Class building a UTC tzinfo object."""

	def utcoffset(self, dt):
		return datetime.timedelta(0)

	def tzname(self, dt):
		return 'UTC'

	def dst(self, dt):
		return datetime.timedelta(0)

	def __repr__(self):
		return "%s()" % self.__class__.__name__

class ThanatosTask:
	comments = {
	"fi00": "arkistoi",
	"fi01": "keskustelun arkistoon",
	"fi01m": "keskustelua arkistoon",
	"fi02": "keskustelun sivulta",
	"fi02m": "keskustelua sivulta",
	}

	name = "archiver"
	# Time min/hour/day/month
	time = ["00/12/*/*", "00/18/*/*", "00/00/*/*", "00/5/*/*"]

	# Database
	db = TinyDB("core/db/taskdb/archiver.json")

	# Archiver config
	template_names = ["Käyttäjä:HarrivBOT/config", "Käyttäjä:4shadowwBOT/config"]

	# Template page object
	template_page = None

	# Execute on start
	exeonstart = True

	def str2time(self, string):
		if string.endswith('d'):
			return datetime.timedelta(days=int(string[:-1]))
		elif string.endswith('h'):
			return datetime.timedelta(hours=int(string[:-1]))
		else:
			return datetime.timedelta(seconds=int(string))

	def get_threads(self, dpage):
		site = pywikibot.Site()
		dpage.threads = []
		start = 0
		cut = False
		ts = textlib.TimeStripper(site=site)
		for l in  range(0, len(dpage.text)):
			thread_header = re.search('^== *([^=].*?) *== *$', dpage.text[l])
			if thread_header:
				if cut == True:
					dpage.threads.append(Thread(dpage.text[start:l], ts))
				start = l
				cut = True
			elif len(dpage.text)-1 == l:
				dpage.threads.append(Thread(dpage.text[start:l+1], ts))

	def removefromlist(self, oldthread, dpage):
		confirmed = False
		i = 0
		startpos = None

		for l in range(0, len(dpage.text)):
			if i == len(oldthread):
				confirmed = True
				break

			if oldthread[i] == dpage.text[l]:
				if startpos == None:
					startpos = l
				i += 1
			else:
				startpos = None
				i = 0

		for l in range(0, len(oldthread)):
			dpage.text.pop(startpos)

	def removeoldt(self, dpage):
		dpage.toarchive = []
		count = len(dpage.threads)
		if len(dpage.oldthreads) >= dpage.config.minthreadstoarchive:
			for thread in dpage.oldthreads:
				if count > dpage.config.minthreadsleft:
					dpage.toarchive.append(thread)
					self.removefromlist(thread.content, dpage)
					count -= 1

	def getpages(self, template):
		site = pywikibot.Site()
		transclusion_page = pywikibot.Page(site, template, ns=10)
		self.template_page = transclusion_page
		return transclusion_page.getReferences(onlyTemplateInclusion=True, follow_redirects=False, namespaces=[])

	def load_config(self, page, site):
		config = Config()
		for tpl in page.templatesWithParams():
			if tpl[0] == pywikibot.Page(site, self.template_name, ns=10):
				for param in tpl[1]:
					item, value = param.split('=', 1)
					if item == "archive":
						now = datetime.datetime.now()
						if "%(year)d" in value:
							value = value.replace("%(year)d", str(now.year))
						elif "%(month)d" in value:
							raise UnsupportedConfig("invalid archive param")
						elif "%(monthname)s" in value:
							raise UnsupportedConfig("invalid archive param")
						elif "%(monthnameshort)s" in value:
							raise UnsupportedConfig("invalid archive param")

						config.archive = value.replace(page.title()+"/", "").replace("{{FULLPAGENAMEE}}/", "")
					elif item ==  "algo":
						if "old(" in value:
							config.algo = re.findall(r"old\((.*?)\)", value)[0]
						else:
							config.algo = value
					elif item == "maxarchivesize":
						config.maxarchivesize = value
					elif item == "minthreadsleft":
						try:
							config.minthreadsleft = int(value)
						except ValueError:
							printlog("invalid minthreadsleft")
					elif item == "minthreadstoarchive":
						try:
							config.minthreadstoarchive = int(value)
						except ValueError:
							printlog("invalid minthreadstoarchive")
					elif item == "archiveheader":
						config.archiveheader = value
					elif item == "counter":
						try:
							config.counter = int(value)
						except ValueError:
							printlog("invalid counter")
					elif item == "key":
						raise UnsupportedConfig("key")
				break
		return config

	def str2bytes(self, string):
		factor = 0
		if "kt" in string or "KT" in string or "kb" in string or "KB":
			factor = 1024
		string = string.replace("K", "").replace("k", "")
		string = string.replace("T", "").replace("t", "")
		string = string.replace("B", "").replace("b", "")
		return int(string)*factor

	def updatecounter(self, template, counter):
		template = template.split("\n")
		for i in range(0, len(template)):
			arr = re.search('^[|].*', template[i])
			if arr:
				arr2 = arr.group(0)[1:].split("=")
				if arr2[0][:7] == "counter":
					arr2[1] = " "+str(counter)
					arr2 = "|"+'='.join(arr2)
					template[i] = arr2
					return '\n'.join(template)


	def addthread2archive(self, dpage, counter):
		x = 0
		site = pywikibot.Site()
		if "%(counter)d" in dpage.config.archive:
			page = pywikibot.Page(site, dpage.name+"/"+dpage.config.archive.replace("%(counter)d", str(counter)))
			using_counter = True
		else:
			page = pywikibot.Page(site, dpage.name+"/"+dpage.config.archive)
			using_counter = False

		if page.exists() == False or page.text == "":
			page.text += dpage.config.archiveheader

		for i in range(0, len(dpage.toarchive)):
			if len(page.text) < self.str2bytes(dpage.config.maxarchivesize) or not using_counter:
				if '\n'.join(dpage.toarchive[0].content) in page.text:
					dpage.toarchive.pop(0)
				else:
					if i == 0:
						page.text += "\n\n"
					page.text += '\n'.join(dpage.toarchive[0].content)+"\n"
					dpage.toarchive.pop(0)
				x += 1

			else:
				counter += 1
				return page, x, counter
		return page, x, counter


	def save2archive(self, dpage):
		archives = []
		usingdb = False

		if dpage.config.counter == None:
			printlog("archiver: counter method db")
			usingdb = True
			exet = Query()
			matches = self.db.search(exet.name == dpage.name)

			if matches == []:
				self.db.insert({"name": dpage.name, "counter": 1})
				counter = 1
			else:
				counter = matches[0]["counter"]
		else:
			printlog("archiver: counter method wikipage")
			counter = dpage.config.counter

		while len(dpage.toarchive) != 0:
			data = self.addthread2archive(dpage, counter)
			if data[1] > 1:
				comment = create_comment.comment([self.comments[config.lang+"00"]+" "+str(data[1])+" "+self.comments[config.lang+"02m"]+" [["+dpage.name+"]]"])
			else:
				comment = create_comment.comment([self.comments[config.lang+"00"]+" yhden "+self.comments[config.lang+"02"]+" [["+dpage.name+"]]"])
			if data[0].text != '\n'.join(dpage.text):
				archives.append(data[0].title())
				printlog("archiver: saving archive "+dpage.name+"/"+dpage.config.archive.replace("%(counter)d", str(counter)))
				wikipedia_worker.savepage(data[0], data[0].text, comment)
				counter = data[2]

		if usingdb:
			self.db.update({"counter": counter}, exet.name == dpage.name)
		else:
			dpage.counter = counter

		strarchives = ""
		for i in range(0, len(archives)):
			strarchives += "[["+archives[i]+"]]"

			if i != len(archives)-1:
				strarchives += ", "

		return strarchives

	def archive(self, dpage, page):
		ac = len(dpage.toarchive)
		archives = self.save2archive(dpage)
		if ac > 1:
			comment = create_comment.comment([self.comments[config.lang+"00"]+" "+str(ac)+" "+self.comments[config.lang+"01m"]+" "+archives])
		else:
			comment = create_comment.comment([self.comments[config.lang+"00"]+" yhden "+self.comments[config.lang+"01"]+" "+archives])

		# Update counter
		if dpage.counter != None and dpage.counter != dpage.config.counter:
			printlog("archiver: have to update counter")
			rx = re.compile(r'\{\{%s\s*?\n.*?\n\}\}'
							% (template_title_regex(self.template_page).pattern), re.DOTALL)
			match = rx.search(page.text).group(0)
			newtemplate = self.updatecounter(match, dpage.counter)
			print(newtemplate)
			dpage.text = '\n'.join(dpage.text).replace(match, newtemplate).split("\n")
		printlog("archiver: saving page")
		wikipedia_worker.savepage(page, '\n'.join(dpage.text), comment)

	def analyze(self, page, dpage):
		dpage.text = page.text.split("\n")
		oldtext = list(dpage.text)
		dpage.oldthreads = []
		self.get_threads(dpage)
		now = datetime.datetime.utcnow().replace(tzinfo=TZoneUTC())
		for thread in dpage.threads:
			if thread.timestamp:
				if now - thread.timestamp > self.str2time(dpage.config.algo):
					dpage.oldthreads.append(thread)

		dpage.oldthreads.sort(key=lambda t: t.timestamp)
		self.removeoldt(dpage)

		if  len(dpage.toarchive) < dpage.config.minthreadstoarchive:
			printlog("archiver: not enough old threads")
			return

		for t in dpage.toarchive:
			printlog("archiver: going to archive",t.content[0])

		if oldtext != dpage.text:
			self.archive(dpage, page)

	def run(self):
		for template in self.template_names:
			self.template_name = template
			pages = self.getpages(template)
			site = pywikibot.Site()
			#pages = [pywikibot.Page(site, "")]
			#self.template_page = pywikibot.Page(site, self.template_name)
			for page in pages:
				printlog("archiver: checking", page)
				try:
					dpage = DiscussionPage()
					dpage.name = page.title()
					dpage.config = self.load_config(page, site)
					dpage.counter = dpage.config.counter
					self.analyze(page, dpage)
				except KeyboardInterrupt:
					return
				except UnsupportedConfig:
					printlog("archiver: skipped", page.title(), "because uc")
				except:
					error = traceback.format_exc()
					printlog("unknown error:\n"+error)
