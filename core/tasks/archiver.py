from core.taskcore import *
import re
from pywikibot import textlib
import datetime
import pywikibot
from tinydb import TinyDB, Query
import traceback
import datetime
from core import path

class UnsupportedConfig(Exception):
	pass

class DiscussionPage:
	def __init__(self):
		self.config = None
		self.text = None
		self.threads = None
		self.oldthreads = []
		self.toarchive = []
		self.page = None
		self.counter = None

class Config:
	def __init__(self):
		self.archive = "Arkisto %(counter)d"
		self.using_year = False
		self.algo = "30d"
		self.counter = None
		self.maxarchivesize = "100kt"
		self.threads = None
		self.minthreadsleft = 5
		self.minthreadstoarchive = 2
		self.archiveheader = "{{Arkisto}}"


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

def glue_template_and_params(template_and_params):
	(template, params) = template_and_params
	text = ""
	for item in params:
		text += u"| %s = %s\n" % (item, params[item])

	return u"{{%s\n%s}}" % (template, text)

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
	time = ["00/04/*/*", "00/12/*/*", "00/18/*/*", "00/00/*/*"]

	# Database
	db = TinyDB(path.main()+"core/db/taskdb/archiver.json")

	# Archiver config
	template_names = ["Käyttäjä:HarrivBOT/config", "Käyttäjä:4shadowwBOT/config"]

	# Template page object
	template_page = None

	# Execute on start
	exeonstart = True

	ignore = []

	site = pywikibot.Site()

	def parse_mas_config(self, value):
		return int(value.replace("t", "").replace("T", "").replace("M", "").replace("m", "").replace("K", "").replace("k", "").replace("B", "").replace("b", ""))

	def load_config(self):
		config = Config()
		for tpl in self.dpage.page.templatesWithParams():
			if tpl[0] == pywikibot.Page(self.site, self.template_name, ns=10):
				for param in tpl[1]:
					item, value = param.split('=', 1)
					if item == "archive":
						now = datetime.datetime.now()
						if "%(year)d" in value:
							value = value.replace("%(year)d", str(now.year))
							config.using_year = True
						elif "%(month)d" in value:
							raise UnsupportedConfig("invalid archive param")
						elif "%(monthname)s" in value:
							raise UnsupportedConfig("invalid archive param")
						elif "%(monthnameshort)s" in value:
							raise UnsupportedConfig("invalid archive param")

						config.archive = value.replace(self.dpage.page.title()+"/", "").replace("{{FULLPAGENAMEE}}/", "")
					elif item ==  "algo":
						if "old(" in value:
							algo = re.findall(r"old\((.*?)\)", value)[0]
							if int(algo.replace("d", "").replace("D", "")) > 0:
								config.algo = algo
						else:
							if int(value.replace("d", "").replace("D", "")) > 0:
								config.algo = value
					elif item == "maxarchivesize":
						try:
							if int(self.parse_mas_config(value)) > 0:
								if "t" in value or "T" in value:
									config.maxarchivesize = value
									config.threads = True
								else:
									config.maxarchivesize = value
									config.threads = False
						except ValueError:
							printlog("invalid maxarchivesize")

					elif item == "minthreadsleft":
						try:
							if int(value) >= 0:
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

	def str2time(self, string):
		if string.endswith('d'):
			return datetime.timedelta(days=int(string[:-1]))
		elif string.endswith('h'):
			return datetime.timedelta(hours=int(string[:-1]))
		else:
			return datetime.timedelta(seconds=int(string))

	def str2bytes(self, string):
		factor = 0
		if "k" in string or "K" in string:
			factor = 1024
		if "m" in string or "M" in string:
			factor = 1048576
		string = string.replace("M", "").replace("m", "")
		string = string.replace("K", "").replace("k", "")
		string = string.replace("B", "").replace("b", "")
		return int(string)*factor

	def updatecounter(self, template, counter):
		template_and_params = textlib.extract_templates_and_params(template)
		for temp in template_and_params:
			if temp[0] == self.template_name and "counter" in temp[1]:
				temp[1]["counter"] = str(counter)
				return glue_template_and_params(temp)

	def getpages(self):
		transclusion_page = pywikibot.Page(self.site, self.template_name, ns=10)
		self.template_page = transclusion_page
		return transclusion_page.getReferences(onlyTemplateInclusion=True, follow_redirects=False, namespaces=[])

	def get_threads(self):
		self.dpage.threads = []
		start = 0
		cut = False
		ts = textlib.TimeStripper(site=self.site)
		for l in  range(0, len(self.dpage.text)):
			thread_header = re.search('^== *([^=].*?) *== *$', self.dpage.text[l])
			if thread_header:
				if cut == True:
					self.dpage.threads.append(Thread(self.dpage.text[start:l], ts))
				start = l
				cut = True
			elif len(self.dpage.text)-1 == l:
				self.dpage.threads.append(Thread(self.dpage.text[start:l+1], ts))

	def removefromlist(self, oldthread):
		confirmed = False
		i = 0
		startpos = None

		for l in range(0, len(self.dpage.text)):
			if i == len(oldthread):
				confirmed = True
				break

			if oldthread[i] == self.dpage.text[l]:
				if startpos == None:
					startpos = l
				i += 1
			else:
				startpos = None
				i = 0

		for l in range(0, len(oldthread)):
			self.dpage.text.pop(startpos)

	def removeoldt(self):
		count = len(self.dpage.threads)
		if len(self.dpage.oldthreads) >= self.dpage.config.minthreadstoarchive:
			for thread in self.dpage.oldthreads:
				if count > self.dpage.config.minthreadsleft:
					self.dpage.toarchive.append(thread)
					self.removefromlist(thread.content)
					count -= 1

	def addthread2archive(self, counter):
		x = 0
		if "%(counter)d" in self.dpage.config.archive:
			page = pywikibot.Page(self.site, self.dpage.page.title()+"/"+self.dpage.config.archive.replace("%(counter)d", str(counter)))
			using_counter = True
		else:
			page = pywikibot.Page(self.site, self.dpage.page.title()+"/"+self.dpage.config.archive)
			using_counter = False

		if not page.exists() or page.text == "":
			page.text += self.dpage.config.archiveheader

		archived = False
		for i in range(len(self.dpage.toarchive)):
			if self.dpage.config.using_year or not self.dpage.config.threads and len(page.text) < self.str2bytes(self.dpage.config.maxarchivesize) or self.dpage.config.threads and self.threads_count(page.text) < self.parse_mas_config(self.dpage.config.maxarchivesize):
				if '\n'.join(self.dpage.toarchive[0].content) in page.text:
					self.dpage.toarchive.pop(0)
				else:
					archived = True
					if i == 0:
						page.text += "\n\n"
					page.text += '\n'.join(self.dpage.toarchive[0].content)+"\n"
					self.dpage.toarchive.pop(0)
					x += 1

			else:
				counter += 1
				return page, x, counter, archived
		return page, x, counter, archived


	def save2archive(self):
		archives = []
		usingdb = False

		if self.dpage.config.counter == None:
			printlog("archiver: counter method db")
			usingdb = True
			exet = Query()
			matches = self.db.search(exet.name == self.dpage.page.title())

			if matches == []:
				self.db.insert({"name": self.dpage.page.title(), "counter": 1})
				counter = 1
			else:
				counter = matches[0]["counter"]
		else:
			printlog("archiver: counter method wikipage")
			counter = self.dpage.config.counter

		while len(self.dpage.toarchive) > 0:
			data = self.addthread2archive(counter)
			if data[1] > 1:
				comment = create_comment.comment([self.comments[config.lang+"00"]+" "+str(data[1])+" "+self.comments[config.lang+"02m"]+" [["+self.dpage.page.title()+"]]"])
			else:
				comment = create_comment.comment([self.comments[config.lang+"00"]+" yhden "+self.comments[config.lang+"02"]+" [["+self.dpage.page.title()+"]]"])
			if data[0].text != '\n'.join(self.dpage.text) and data[3]:
				archives.append(data[0].title())
				printlog("archiver: saving archive "+self.dpage.page.title()+"/"+self.dpage.config.archive.replace("%(counter)d", str(counter)))
				wikipedia_worker.savepage(data[0], data[0].text, comment)
				counter = data[2]
			elif data[2] > counter:
				counter = data[2]

		if usingdb:
			self.db.update({"counter": counter}, exet.name == self.dpage.page.title())
		else:
			self.dpage.counter = counter

		strarchives = ""
		for i in range(len(archives)):
			strarchives += "[["+archives[i]+"]]"

			if i != len(archives)-1:
				strarchives += ", "

		return strarchives

	def archive(self):
		ac = len(self.dpage.toarchive)
		archives = self.save2archive()
		if ac > 1:
			comment = create_comment.comment([self.comments[config.lang+"00"]+" "+str(ac)+" "+self.comments[config.lang+"01m"]+" "+archives])
		else:
			comment = create_comment.comment([self.comments[config.lang+"00"]+" yhden "+self.comments[config.lang+"01"]+" "+archives])

		# Update counter
		if self.dpage.counter != None and self.dpage.counter != self.dpage.config.counter:
			printlog("archiver: have to update counter")
			rx = re.compile(r'\{\{%s\s*?\n.*?\n\}\}'
							% (template_title_regex(self.template_page).pattern), re.DOTALL)
			match = rx.search(self.dpage.page.text).group(0)
			newtemplate = self.updatecounter(match, self.dpage.counter)
			self.dpage.text = '\n'.join(self.dpage.text).replace(match, newtemplate).split("\n")
		printlog("archiver: saving page")
		wikipedia_worker.savepage(self.dpage.page, '\n'.join(self.dpage.text), comment)


	def shouldArchive(self):
		self.dpage.text = self.dpage.page.text.split("\n")
		oldtext = list(self.dpage.text)
		self.get_threads()
		now = datetime.datetime.utcnow().replace(tzinfo=TZoneUTC())
		for thread in self.dpage.threads:
			if thread.timestamp:
				if now - thread.timestamp > self.str2time(self.dpage.config.algo):
					self.dpage.oldthreads.append(thread)

		self.dpage.oldthreads.sort(key=lambda t: t.timestamp)
		self.removeoldt()

		if  len(self.dpage.toarchive) < self.dpage.config.minthreadstoarchive:
			printlog("archiver: not enough old threads")
			return False

		for t in self.dpage.toarchive:
			printlog("archiver: going to archive",t.content[0])

		if oldtext != self.dpage.text:
			return True


	def run(self):
		for template in self.template_names:
			self.template_name = template
			pages = self.getpages()
			#pages = [pywikibot.Page(self.site, "Keskustelu wikiprojektista:Urheilu")]
			#self.template_page = pywikibot.Page(self.site, self.template_name)
			for page in pages:
				if page.title() in self.ignore:
					print("ignored", page.title())

				elif page.botMayEdit() and page.canBeEdited():
					printlog("archiver: checking", page)
					try:
						self.dpage = DiscussionPage()
						self.dpage.page = page
						self.dpage.config = self.load_config()
						self.dpage.counter = self.dpage.config.counter
						if self.shouldArchive():
							self.archive()

					except KeyboardInterrupt:
						return
					except UnsupportedConfig:
						printlog("archiver: skipped", page.title(), "because uc")
					except:
						error = traceback.format_exc()
						crashreport(error)
						printlog("unknown error:\n"+error)
