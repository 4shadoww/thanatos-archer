import pywikibot
from pywikibot import pagegenerators
import core.config

def loadpage(page):
	try:
		site = pywikibot.Site()
		site.throttle.setDelays(core.config.api_delay=0, core.config.api_writedelay=5, core.config.api_absolute=False)
		wpage = pywikibot.Page(site, page)

	except pywikibot.exceptions.InvalidTitle:
		return

	return site, wpage

def savepage(wpage, text, comment):
	if core.config.test == False:
		try:
			wpage.text = text
			wpage.save(comment)

		except pywikibot.exceptions.EditConflict:
			printlog("edit conflict not saved", wpage)
		except pywikibot.exceptions.OtherPageSaveError:
			printlog("other page save error not saved", wpage)
