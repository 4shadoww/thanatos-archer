from core import config

lang = {
	"fi_bot": "Botti",
	"fi_and": "ja"
}


def comment(comments):
	full_comment = u""
	i = 0
	for comment in comments:
		if i == 0:
			full_comment += lang[config.lang+"_bot"]+" "

		full_comment += comment

		if i == len(comments)-1:
			full_comment += "."

		elif i == len(comments)-2:
			full_comment += ", "+lang[config.lang+"_and"]+" "

		else:
			full_comment += ", "

		i += 1
	return full_comment