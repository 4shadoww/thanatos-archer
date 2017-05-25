# - *- coding: utf- 8 - *-
from core.taskcore import *
import traceback
from tinydb import TinyDB, Query
import pywikibot
import re

class Config:
	archive = "Arkisto %(counter)d"
	style = "simple"
	linktext = "Arkisto, osa %(counter)d"

class LinkGenerator:
	def simple(self, links, config):
		counter = 1
		string = ""
		for link in links:
			string += "* [["+link+"|"+config.linktext.replace("%(counter)d", str(counter))+"]]\n"
			counter += 1
		return string

	def oneline(self, links, config):
		counter = 1
		string = ""
		for link in links:
			if counter != len(links):
				string += "[["+link+"|"+config.linktext.replace("%(counter)d", str(counter))+"]] • "
			else:
				string += "[["+link+"|"+config.linktext.replace("%(counter)d", str(counter))+"]]"
			counter += 1
		return string

	def box(self, links, config):
		counter = 1
		string = "{| class=\"infobox\" align=\"right\" style=\"text-align:center\"\n|-\n! colspan=\"3\" | [[Kuva:Filing cabinet icon.svg|50px|Arkistot]]\n|-\n"

		for link in links:
			string += "| [["+link+"|"+config.linktext.replace("%(counter)d", str(counter))+"]]\n"
			if counter != len(links):
				string += "|-\n"
			counter += 1
		string += "|}\n"
		return string

	def generate(self, config, links):
		if config.style == "simple":
			return self.simple(links, config)
		elif config.style == "box":
			return self.box(links, config)
		elif config.style == "oneline":
			return self.oneline(links, config)
		else:
		 	return self.simple(links, config)

class ThanatosTask:
	name = "archive_linker"
	# Time min/hour/day/month
	time = ["00/*/*/*"]

	# Template name
	template_name = "Käyttäjä:4shadowwBOT/linker"

	# Template Page
	template_page = None

	# Execute on start
	exeonstart = True

	# Html tags
	stag = "<div class=4linker>"
	etag = "</div>"

	comments = {
		"fi": ": päivitetty arkistolinkit",
	}

	db = TinyDB("core/db/taskdb/archiver_linker.json")

	def load_config(self, page, site):
		confg = Config()
		for tpl in page.templatesWithParams():
			if tpl[0] == pywikibot.Page(site, self.template_name, ns=10):
				for param in tpl[1]:
					item, value = param.split('=', 1)
					if item == "archive":
						config.archive = value
					elif item == "style":
						config.style = value
					elif item == "linktext":
						config.linktext = value
				break
		return config

	def template_title_regex(self, tpl_page):
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

	def getpages(self):
		site = pywikibot.Site()
		transclusion_page = pywikibot.Page(site, self.template_name, ns=10)
		self.template_page = transclusion_page
		return transclusion_page.getReferences(onlyTemplateInclusion=True, follow_redirects=False, namespaces=[])

	def get_links(self, page, site, config):
		query = Query()
		links = []
		counter = 1
		while True:
			apage =  pywikibot.Page(site, page.title()+"/"+config.archive.replace("%(counter)d", str(counter)))
			if apage.exists() and apage.text != "":
				links.append(apage.title())
			else:
				self.db.update({"counter": counter-1}, query.name == page.title())
				break
			counter += 1
		return links

	def update_text(self, page, linktable):
		if self.stag in page.text:
			reg = self.stag+".*?"+"<\/div>"
			oldtable = re.findall(reg, page.text, re.DOTALL)
			page.text = page.text.replace(oldtable[0], self.stag+"\n"+linktable+self.etag)
		else:
			rx = re.compile(r'\{\{%s\s*?\n.*?\n\}\}'
							% (self.template_title_regex(self.template_page).pattern), re.DOTALL)
			match = rx.search(page.text).group(0)
			if match:
				match = match.split("\n")
				textlist = page.text.split("\n")
				x = 0
				placepos = 0
				for i in range(0, len(textlist)):
					if match[x] in textlist[i]:
						if x == len(match)-1:
							placepos = i
							break
						x += 1
				textlist[placepos] = textlist[placepos]+"\n"+self.stag+"\n"+linktable+self.etag
				page.text = '\n'.join(textlist)

	def link(self, page, site, config):
			query = Query()
			match = self.db.search(query.name == page.title())
			must_update = False

			if match == []:
				self.db.insert({"name": page.title(), "counter": 1})
				match = self.db.search(query.name == page.title())
				must_update = True
			else:
				apage =  pywikibot.Page(site, page.title()+"/"+config.archive.replace("%(counter)d", str(match[0]["counter"]+1)))
				if apage.exists() and apage.text != "":
					must_update = True
			if must_update:
				printlog("archive linker: checking links for", page)
				oldtext = page.text
				links = self.get_links(page, site, config)
				lg = LinkGenerator()
				linktable = lg.generate(config, links)
				self.update_text(page, linktable)
				newmatch = self.db.search(query.name == page.title())

				comment = create_comment.comment([self.comments[config.lang]])
				if oldtext != page.text:
					printlog("archive linker: updating links for", page)
					wikipedia_worker.savepage(page, page.text, comment)

	def run(self):
		pages = self.getpages()
		site = pywikibot.Site()
		#pages = [pywikibot.Page(site, "Keskustelu käyttäjästä:4shadoww")]
		for page in pages:
			if page.botMayEdit() and page.canBeEdited():
				printlog("archive linker: checking", page)
				try:
					config = self.load_config(page, site)
					self.link(page, site, config)
				except KeyboardInterrupt:
					return
				except:
					error = traceback.format_exc()
					printlog("unknown error:\n"+error)
