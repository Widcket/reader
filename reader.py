"""
	This little app was made for Programmr's "News Reader 2013" contest.
	What it tries to do is to present the top 3 news from CNN, ABC and NBC that belong to a a set of
	shared/common topics between these 3 news sites, ordered by occurrences (number of news of each topic).
	Works by fetching the Top Stories feeds from CNN, ABC and NBC, stripping some common words from the titles,
	then filtering the title words that are most common in the 3 feeds, selecting the top 3 topics,
	then picking a random new item from each topic and displaying the result.
"""

from bottle import route, run, template
from random import choice, shuffle
import feedparser
import re

@route('/')
def index():
	#------------------------- Fetching the feeds -------------------------
	class Feed():
		def __init__(self, feed, name):
			self.feed = feedparser.parse(feed)
			self.name = name
			self.len = len(self.feed["entries"])
			self.tmap = []

		def __len__(self):
			return len(self.tmap)


	cnn = Feed("http://rss.cnn.com/rss/edition.rss", "CNN")
	abc = Feed("http://feeds.abcnews.com/abcnews/topstories", "ABC News")
	nbc = Feed("http://feeds.nbcnews.com/feeds/topstories", "NBC News")

	# Just in case
	if cnn.feed["status"] == 404 or cnn.feed["status"] == 500 or cnn.feed["status"] == 503:
		return "Couldn't load CNN feed"
	if abc.feed["status"] == 404 or abc.feed["status"] == 500 or abc.feed["status"] == 503:
		return "Couldn't load ABC feed"
	if nbc.feed["status"] == 404 or nbc.feed["status"] == 500 or nbc.feed["status"] == 503:
		return "Couldn't load NBC feed"

	#------------------------- Stripping the common words -------------------------

	common_words = ("the", "and", "a", "that", "I", "it", "not", "he", "as", "you", "this", "but",
	                "his", "they", "her", "she", "or", "an", "will", "my", "one", "all", "would",
	                "there", "their", "to", "of", "in", "for", "on", "with", "at", "by", "from",
	                "up", "about", "into", "over", "after", "beneath", "under", "above", "is", "was",
	                "were", "are", "at", "then", "off", "if", "no", "can", "can't", "what", "when",
	                "who", "whom", "won't", "don't", "ain't", "it", "theirs", "yet", "be", "could",
	                "couldn't", "how", "do", "does", "did", "say", "says", "said", "u", "you", "yours", "his", "hers", "its", "before",
	                "after", "onto", "more", "less", "have", "has", "has", "do", "use", "also",
					"each", "other", "which", "them", "many", "so", "then", "some", "make", "like",
					"been", "may", "made", "come", "get", "look", "first", "down", "did", "going",
					"didn't", "hasn't", "haven't", "not", "only", "any", "because", "most", "give",
					"want", "new", "well", "our", "back", "in", "out")

	punctuation = ("?", "!", ".", ",", ";", ":", "...", "'s", "'ve" ".com")

	first_strip = re.compile('|'.join(map(re.escape, punctuation)))
	second_strip = re.compile(r'\b%s\b' % r'\b|\b'.join(map(re.escape, common_words)))


	def strip(obj):
		for i in xrange(0, obj.len):
			title = obj.feed["entries"][i].title
			lc_title = title.lower()
			title_words = first_strip.sub("", lc_title)
			title_words = set(second_strip.sub("", title_words).split())
			obj.tmap.append([title_words, title, obj.feed["entries"][i].link, obj.name])

	strip(cnn)
	strip(abc)
	strip(nbc)

	#------------------------- Deciding the filtering order -------------------------

	# Shortest one goes first
	if len(cnn) < len(abc) and len(cnn) < len(nbc):
		master = cnn
		if len(abc) < len(nbc):
			slave1 = abc
			slave2 = nbc
		else:
			slave1 = nbc
			slave2 = abc
	elif len(abc) < len(cnn) and len(abc) < len(nbc):
		master = abc
		if len(cnn) < len(nbc):
			slave1 = cnn
			slave2 = nbc
		else:
			slave1 = nbc
			slave2 = cnn
	else:
		master = nbc
		if len(cnn) < len(abc):
			slave1 = cnn
			slave2 = abc
		else:
			slave1 = abc
			slave2 = cnn

	#------------------------- Filtering the title words -------------------------

	master.matches = []

	# first feed vs second feed
	for i in xrange(0, len(master)):
		for k in xrange(0, len(slave1)):
			match = master.tmap[i][0].intersection(slave1.tmap[k][0])

			if match:
				master.matches.append(match)

	master.second_matches = {}

	# result of last filtering vs last feed
	for i in xrange(0, len(master.matches)):
		for k in xrange(0, len(slave2)):
			second_match = master.matches[i].intersection(slave2.tmap[k][0])

			if second_match:
				second_match = " ".join(second_match)

				if second_match not in master.second_matches:
					master.second_matches[second_match] = 1
				else:
					master.second_matches[second_match] += 1

	# picking the top 3 topics
	master.second_matches = sorted(master.second_matches, key=master.second_matches.get, reverse=True)[:3]

	#------------------------- Populating the topics -------------------------

	topic1 = []
	topic2 = []
	topic3 = []

	def filter_news(obj):
		# case of topics composed by more than one word, represented as a list
		for item in master.second_matches:
			if " " in item:
				master.second_matches[item] = item.split()
		for item in obj.tmap:
			if type(master.second_matches[0]) is list:
				if all(words in item[0] for words in master.second_matches[0]):
					item[0] = " #".join(master.second_matches[0])
					topic1.append(item)
			elif type(master.second_matches[1]) is list:
				if all(words in item[0] for words in master.second_matches[1]):
					item[0] = " #".join(master.second_matches[1])
					topic2.append(item)
			elif type(master.second_matches[2]) is list:
				if all(words in item[0] for words in master.second_matches[2]):
					item[0] = " #".join(master.second_matches[2])
					topic3.append(item)
			else:
				# one word topics
				if master.second_matches[0] in item[0]:
					item[0] = master.second_matches[0]
					topic1.append(item)
				elif master.second_matches[1] in item[0]:
					item[0] = master.second_matches[1]
					topic2.append(item)
				elif master.second_matches[2] in item[0]:
					item[0] = master.second_matches[2]
					topic3.append(item)

	#------------------------- Picking the random winners -------------------------

	filter_news(cnn)
	filter_news(abc)
	filter_news(nbc)

	shuffle(topic1)
	shuffle(topic2)
	shuffle(topic3)

	results = [choice(topic1), choice(topic2), choice(topic3)]

	#------------------------- Delivering the result -------------------------

	return template('template.html', items=results)

run(host='localhost', port=8080)
