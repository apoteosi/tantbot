# -*- coding: utf-8 -*-

import wikipedia as wiki
import pronouncing
from newsapi import NewsApiClient
import urllib2
from urlparse import urlparse
from urlparse import parse_qs
import json
from pygtail import Pygtail
from bs4 import BeautifulSoup, SoupStrainer
import os
import sys
import traceback
import subprocess
import time
import random
import tweepy
import re
import requests
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
import pycorpora as corp
import basc_py4chan

###############  FUNC  ###############

def send(room, msg):
	msg = msg.replace('\n', '\n/me | ')
	subprocess.call('museekcontrol --chat "%s" --message "/me | %s"' % (room, msg), shell=True)



def sylco(word) :

	word = word.lower()

	# exception_add are words that need extra syllables
	# exception_del are words that need less syllables

	exception_add = ['serious','crucial']
	exception_del = ['fortunately','unfortunately']

	co_one = ['cool','coach','coat','coal','count','coin','coarse','coup','coif','cook','coign','coiffe','coof','court']
	co_two = ['coapt','coed','coinci']

	pre_one = ['preach']

	syls = 0 #added syllable number
	disc = 0 #discarded syllable number

	#1) if letters < 3 : return 1
	if len(word) <= 3 :
		syls = 1
		return syls

	#2) if doesn't end with "ted" or "tes" or "ses" or "ied" or "ies", discard "es" and "ed" at the end.
	# if it has only 1 vowel or 1 set of consecutive vowels, discard. (like "speed", "fled" etc.)

	if word[-2:] == "es" or word[-2:] == "ed" :
		doubleAndtripple_1 = len(re.findall(r'[eaoui][eaoui]',word))
		if doubleAndtripple_1 > 1 or len(re.findall(r'[eaoui][^eaoui]',word)) > 1 :
			if word[-3:] == "ted" or word[-3:] == "tes" or word[-3:] == "ses" or word[-3:] == "ied" or word[-3:] == "ies" :
				pass
			else :
				disc+=1

	#3) discard trailing "e", except where ending is "le"  

	le_except = ['whole','mobile','pole','male','female','hale','pale','tale','sale','aisle','whale','while']

	if word[-1:] == "e" :
		if word[-2:] == "le" and word not in le_except :
			pass

		else :
			disc+=1

	#4) check if consecutive vowels exists, triplets or pairs, count them as one.

	doubleAndtripple = len(re.findall(r'[eaoui][eaoui]',word))
	tripple = len(re.findall(r'[eaoui][eaoui][eaoui]',word))
	disc+=doubleAndtripple + tripple

	#5) count remaining vowels in word.
	numVowels = len(re.findall(r'[eaoui]',word))

	#6) add one if starts with "mc"
	if word[:2] == "mc" :
		syls+=1

	#7) add one if ends with "y" but is not surrouned by vowel
	if word[-1:] == "y" and word[-2] not in "aeoui" :
		syls +=1

	#8) add one if "y" is surrounded by non-vowels and is not in the last word.

	for i,j in enumerate(word) :
		if j == "y" :
			if (i != 0) and (i != len(word)-1) :
				if word[i-1] not in "aeoui" and word[i+1] not in "aeoui" :
					syls+=1

	#9) if starts with "tri-" or "bi-" and is followed by a vowel, add one.

	if word[:3] == "tri" and word[3] in "aeoui" :
		syls+=1

	if word[:2] == "bi" and word[2] in "aeoui" :
		syls+=1

	#10) if ends with "-ian", should be counted as two syllables, except for "-tian" and "-cian"

	if word[-3:] == "ian" : 
	#and (word[-4:] != "cian" or word[-4:] != "tian") :
		if word[-4:] == "cian" or word[-4:] == "tian" :
			pass
		else :
			syls+=1

	#11) if starts with "co-" and is followed by a vowel, check if exists in the double syllable dictionary, if not, check if in single dictionary and act accordingly.

	if word[:2] == "co" and word[2] in 'eaoui' :

		if word[:4] in co_two or word[:5] in co_two or word[:6] in co_two :
			syls+=1
		elif word[:4] in co_one or word[:5] in co_one or word[:6] in co_one :
			pass
		else :
			syls+=1

	#12) if starts with "pre-" and is followed by a vowel, check if exists in the double syllable dictionary, if not, check if in single dictionary and act accordingly.

	if word[:3] == "pre" and word[3] in 'eaoui' :
		if word[:6] in pre_one :
			pass
		else :
			syls+=1

	#13) check for "-n't" and cross match with dictionary to add syllable.

	negative = ["doesn't", "isn't", "shouldn't", "couldn't","wouldn't"]

	if word[-3:] == "n't" :
		if word in negative :
			syls+=1
		else :
			pass   

	#14) Handling the exceptional words.

	if word in exception_del :
		disc+=1

	if word in exception_add :
		syls+=1	 

	# calculate the output
	return numVowels - disc + syls


#dictionary search, maybe instead of return, return a list at the end. to have multiple defs.
def find(x):
	srch=str(x)
	try:
		x=urllib2.urlopen("http://dictionary.reference.com/browse/"+srch+"?s=t")
		x=x.read()
		items=re.findall('<meta name="description" content="'+".*$",x,re.MULTILINE)
		for x in items:
			y=x.replace('<meta name="description" content="','')
			z=y.replace(' See more."/>','')
			m=re.findall('at Dictionary.com, a free online dictionary with pronunciation,			  synonyms and translation. Look it up now! "/>',z)
			if m==[]:
				if z.startswith("Get your reference question answered by Ask.com"):
					return "not a real word dummy"
				else:
					p, _ = z.rsplit("See ", 1)
					p = p.replace(" definition, ", ": ", 1)
					return p
		else:
				return "not a real word dummy"
	except urllib2.HTTPError:
		return "not a real word dummy"

def yt_title(vid):
	url = "https://www.googleapis.com/youtube/v3/videos?part=snippet&id={id}&key={api_key}"
	_id = vid
	DEVELOPER_KEY = 'AIzaSyAf0eEylmI92OYQwTJKEOSVVM4geDMGO_0'
	r = requests.get(url.format(id=_id, api_key=DEVELOPER_KEY))
	js = r.json()
	try:
		items = js["items"][0]
		return (items["snippet"]["title"])
	except IndexError:
		return ''

def video_id(value):
	"""
	Examples:
	- http://youtu.be/SA2iWivDJiE
	- http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
	- http://www.youtube.com/embed/SA2iWivDJiE
	- http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
	"""
	query = urlparse(value)
	if query.hostname == 'youtu.be':
		return query.path[1:]
	if query.hostname in ('www.youtube.com', 'youtube.com'):
		if query.path == '/watch':
			p = parse_qs(query.query)
			return p['v'][0]
		if query.path[:7] == '/embed/':
			return query.path.split('/')[2]
		if query.path[:3] == '/v/':
			return query.path.split('/')[2]
	# fail?
	return None

def commands(room, line):
	try:
		# parse code
		a, b = line.split("]", 1)
		b = b[1:] #remove leading space

		_, name = a.split("[")

		#test function
		if ((b=="!test\n") and ("mars" in a)):
			if room == "mutants":
				send(room, "we out here")
			if room == "star fish":
				send(room, "beep")


		#listing of available commands
		if b=="!commands\n":
			if room == "mutants":
				send(room, '!addquote *** !quote !req *** !t *** !hi !art !art ***\n!news !news *** !dev *** !clap *** !def *** !sandwich !diagnose !oracle !slap [user]\n!movie *** !listmovies !sonnet !chuck !dog !qotd !haiku !wiki !advice !link')
			if room == "star fish":				
				send(room, '!addquote *** !quote !req *** !t *** !hi !art !art ***\n!news !news *** !dev *** !clap *** !def *** !sandwich !diagnose !oracle !slap ***\n!movie *** !listmovies !sonnet !chuck !dog !qotd !haiku !wiki !advice !link !startup')
			
		#request features, appends to local requests.log
		if b.startswith("!req "):
			send(room, "thank you very much")
			req = open("requests.log", "a+")
			req.write(line)
			req.close()
			print "request added:"
			print b

		#intestination --- get console output from list users, find if it contains user
		#user found -- shall i intestinate? (yes/no)
		if b.startswith("!intestinate "):
			_, usr = b.split(1)
			send(room, "/me")

		#thanks
		if b=="thanks\n":
			send(room, "you too")

		#quote database (add specific users)
		if b.startswith("!addquote "):
			if room == "mutants":
				quotes = open("quotes.log", "a+")
			if room == "star fish":
				quotes = open("starquotes.log", "a+")
			_, q = b.split(' ', 1)
			quotes.write(q)
			quotes.close()
			send(room, "quote added!")

		if b=="!quote\n":
			if room == "mutants":
				lines = open('quotes.log').read().splitlines()
			if room == "star fish":
				lines = open('starquotes.log').read().splitlines()
			randquote = random.choice(lines)
			send(room, randquote)

		#link aggregator
		if "http" in b:
			c = b.find("http")

		#twitter feed
		if b=="!tweet\n":
			if room == "mutants":
				tweets = api.home_timeline(count=1)
				for t in tweets:
					send(room, t.text)

		if b.startswith("!t "):
			acct = b[3:].strip()
			works = 1
			try:
				tweets = api.user_timeline(id=acct,count=500,tweet_mode='extended')
			except tweepy.error.TweepError:
				send(room, "u fucked up")
				works = 0
			if works == 1:
				tt = True
				while tt == True:
					tt = False
					t = random.choice(tweets)
					try:
						text = t.extended_tweet["full_text"]
					except AttributeError:
						try:
							text = t.text
						except AttributeError:
							text = t.full_text
					if ("RT @" not in text) and (not text.startswith("@")):
						send(room, text)
					else:
						tt = True

		if b=="!usa\n":
			usalist = ["USA","USAUSA","USAUSAUSA","USAUSAUSAUSA","U\nS\nA\n","USA USA USA USA USA","UUU\nSSS\nAAA"]
			for _ in range(0, 10):
				c = random.randint(0, 6)
				send(room, usalist[c])
				time.sleep(1)


		if b=="!rand\n":
			if room == "mutants":
				tweets = api.user_timeline(count=50)
				t = random.choice(tweets)
				send(room, t.text)

		if re.match('!rand [0-9]', b):
			if room == "mutants":
				num = int(b[6])
				tweets = api.user_timeline(count=500)
				for _ in range(0, num):
					t = random.choice(tweets)
					send(room, t.text)
					time.sleep(1.5)

		#dgd link spammer
		if ((b=="!dgd\n") and ("(o" in a)):
			links = open('dgd.txt').read().splitlines()
			randlink = random.choice(links)
			send(room, randlink)

		#hi test
		if b=="!hi\n":
			send(room, u"hi, %s 🐙" % name)

		if b=="!benny\n":
			send(room, "benny")

		#definitions
		if b.startswith("!def "):
			f = find(b[5:].strip())
			send(room, f)

		#news api
		if b.startswith("!news "):
			query = b[6:].strip()
			allnews = newsapi.get_everything(q=query,page_size=50)
			length = len(allnews['articles'])
			if length != 0:
				if length > 2:
					num = random.randint(0,length-1)
				elif length == 1:
					num = 0
				send(room, allnews['articles'][num]['title'])
				time.sleep(1)
				send(room, allnews['articles'][num]['description'])
				time.sleep(1)
				send(room, allnews['articles'][num]['url'])
			else:
				send(room, "none found")

		if b=="!news\n":
			topnews = newsapi.get_top_headlines(sources='bbc-news',page_size=50)
			num = random.randint(0,topnews['totalResults']-1)
			send(room, topnews['articles'][num]['title'])
			time.sleep(1)
			send(room, topnews['articles'][num]['description'])
			time.sleep(1)
			send(room, topnews['articles'][num]['url'])

		#deviantart
		if b.startswith("!dev "):
			query = b[5:].strip()
			allnews = newsapi.get_everything(q=query,page_size=50, domains='deviantart.com')
			length = len(allnews['articles'])
			if length != 0:
				if length > 2:
					num = random.randint(0,length-1)
				else:
					num = 0
					
				if num > 0:
					send(room, allnews['articles'][num]['title'])
					time.sleep(1)
					send(room, allnews['articles'][num]['description'])
					time.sleep(1)
					send(room, allnews['articles'][num]['url'])
			else:
				send(room, "none found")


		#wikiart retrieval
		if b=="!art\n":  #random from most popular
			url = urllib2.urlopen('https://www.wikiart.org/en/App/Painting/MostViewedPaintings?randomSeed=123&json=2')
			urldict = json.load(url)
			r = random.randint(0, len(urldict)-1)
			title = urldict[r]['title']
			artist = urldict[r]['artistName']
			image = urldict[r]['image']
			year = urldict[r]['completitionYear']
			image = image.replace('!Large.jpg', '')

			send(room, title + ' [' + artist + ', ' + str(year) + ']')
			send(room, image)

		if b.startswith("!art "):
			query = b[5:].strip()
			query = query.replace(' ', '%20')
			url = urllib2.urlopen('https://www.wikiart.org/en/search/%s/1?json=2&PageSize=600' % query)
			urldict = json.load(url)
			if (len(urldict) != 0):
				if (len(urldict) == 1):
					r = 0
				elif (len(urldict) > 1):
					r = random.randint(0, len(urldict)-1)
				title = urldict[r]['title']
				artist = urldict[r]['artistName']
				image = urldict[r]['image']
				year = urldict[r]['completitionYear']
				image = image.replace('!Large.jpg', '')

				send(room, title + ' [' + artist + ', ' + str(year) + ']')
				send(room, image)
			else:
				send(room, "none found")

		#clap emoji converter
		if b.startswith("!clap "):
			text = b[6:]
			claptext = "👏 " + text.replace(' ', ' 👏 ').strip('\n') + ' 👏'
			send(room, claptext)

		#gross
		if b=="!brap\n":
			send(room, "BRRRRAAAAAAAP")

		#youtube link title
		if (('watch?v' in b) or ('youtu.be' in b)) and ('~' not in b):
			if room == "mutants":
				last_id_tants = video_id(b)
			if room == "star fish":
				last_id_star = video_id(b)
			title = yt_title(video_id(b))
			if title != '':
				send(room, title)

		if b=="!y\n":
			if room == "mutants":
				lastid = last_id_tants
			if room == "star fish":
				lastid = last_id_star
			if lastid != '':
				send(room, yt_title(lastid))

		if b=="!sandwich\n":
			wich = random.choice(corp.foods.sandwiches['sandwiches'])
			send(room, wich['name'])
			time.sleep(0.5)
			send(room, wich['description'])
			time.sleep(0.5)
			if wich['origin'] != '':
				send(room, 'Origin: ' + wich['origin'])

		if b=="!diagnose\n":
			options = ["good news! you have {disease} from that {animal} in {country}","i'm sorry, you've contracted {disease} from a {animal} in {country}"]
			sentence = random.choice(options)
			_disease=random.choice(corp.medicine.diagnoses['codes'])['desc']
			_disease = _disease[0].lower() + _disease[1:]
			_animal=random.choice(corp.animals.common['animals'])
			_country=random.choice(corp.geography.countries['countries'])
			send(room, sentence.format(disease=_disease,animal=_animal,country=_country))

		if b=="!oracle\n":
			oracles = open('oracle.txt').read().splitlines()
			randlink = random.choice(oracles)
			send(room, randlink)

		if b.startswith("!slap "):
			victim = b[6:].strip("\n")
			verbs = ['slaps','smacks','bludgeons','uppercuts']
			_verb = random.choice(verbs)
			_obj = random.choice(corp.objects.objects['objects'])
			if _obj[0] in ['a','e','i','o','u']:
				_article = 'an'
			else:
				_article = 'a'
			send(room, '%s %s %s with %s %s.' % (name, _verb, victim, _article, _obj))

		if b=="!goatse\n":
			lines = open("goatse.txt").read().splitlines()
			for l in lines:
				send(room, l)

		if ("elma" in b) and ("elma" not in name) and ("tant" not in name):
			if room == "mutants":
				send(room, "it's Elma now")

		#request muvies
		if b.startswith("!movie "):
			send(room, "i added it thanks")
			if room=="mutants":
				req = open("muvies.log", "a+")
			elif room=="star fish":
				req = open("starmuvies.log", "a+")
			req.write(b[7:])
			req.close()
			print "movie added:"
			print b

		if b=="!listmovies\n":
			
			if room=="mutants":
				ms = open("muvies.log").read().splitlines()
			elif room=="star fish":
				ms = open("starmuvies.log").read().splitlines()
			send(room, "movie list:")
			for m in ms:
				send(room, m)

		if b=="!sonnet\n":
			r = requests.get("http://poetrydb.org/author,linecount/Shakespeare;14/title,lines")
			r = r.json()
			sonnet = random.choice(r)
			for l in sonnet['lines']:
				send(room, l)

		if b=="!chuck\n":
			r = requests.get("https://api.chucknorris.io/jokes/random")
			r = r.json()
			send(room, r['value'])

		if b=="!dog\n":
			r = requests.get("https://dog.ceo/api/breeds/image/random")
			r = r.json()
			send(room, r['message'])
		if b=="!qotd\n":
			r = requests.get("https://favqs.com/api/qotd")
			r = r.json()
			send(room, '%s - %s' % (r['quote']['body'], r['quote']['author']))
		if (sylco(b) > 5) and (sylco(b) < 12) and ("tant" not in name):
			if (random.randint(0, 300) == 2) or (b.startswith("   ")):
				if (room == "mutants") or (room == "star fish"):
					word = b.rsplit(None, 1)[-1].lower()
					print word
					rhymes = pronouncing.rhymes(word)
					print rhymes
					if room=="mutants":
						slines = open("mutants.log").read().splitlines()
					if room=="star fish":
						slines = open("star fish.log").read().splitlines()
					random.shuffle(slines)
					for sline in slines:
						lastword = sline.rsplit(None, 1)[-1]
						if lastword in rhymes:
							if sylco(sline.rsplit(']', 1)[-1][1:]) == sylco(b):
								send(room, "ay")
								time.sleep(1)
								rhyming = sline.split(']',1)[-1]
								print rhyming
								send(room, rhyming.strip('\n'))
								time.sleep(1)
								send(room, "ay")
								break

		#log haiku generator
		if b=="!haiku\n":
			slines = open("%s.log" % room).read().splitlines()
			random.shuffle(slines)
			line1 = ''
			line2 = ''
			line3 = ''
			for sline in slines:
				text = sline.rsplit(']',1)[-1][1:]
				if sylco(text)==5:
					if line1 == '':
						line1 = text
					else:
						line3 = text
						break
			for sline in slines:
				text = sline.rsplit(']',1)[-1][1:]
				if sylco(text)==7:
					line2 = text
			send(room, line1)
			time.sleep(1)
			send(room, line2)
			time.sleep(1)
			send(room, line3)

		if b=="!wiki\n":
			list = wiki.random()
			page = wiki.page(title=list)
			send(room, page.url)

		if b=="!advice\n":
			r = requests.get("http://api.adviceslip.com/advice")
			r = r.json()
			send(room, r['slip']['advice'])

		if b=="!link\n":
			slines = open("%s.log" % room).read().splitlines()
			random.shuffle(slines)
			for line in slines:
				links = ''
				f = re.search("(?P<url>https?://[^\s]+)", line)
				if f:
					f = f.group('url')
					send(room, f)
					break

		if b=="!startup\n":
			r = requests.get("http://itsthisforthat.com/api.php?text")
			r = r.text
			send(room, r)

		#4chan random topic
		if b.startswith("!chan "):
			boardname = b[6:].strip('\n')
			board = basc_py4chan.Board(boardname)
			threads = board.get_all_thread_ids()
			threadid = random.choice(threads)
			thread = board.get_thread(threadid)
			images = thread.files()
			#topic = thread.topic
			#imgfile = topic.first_file
			#print topic.comment
			#print imgfile.file_url
			for f in thread.files():
				send(room, f)
				break

		#twitter search
		if b.startswith("!twit "):
			query = b[6:].strip('\n')
			tweets = api.search(query)
			while 1:
				tweet = random.choice(tweets)
				if 'RT' not in tweet.text:
					if tweet.text[0] != '@':
						break
			send(room, tweet.text)

		if b=="!fortune\n":
			r = requests.get("http://fortunecookieapi.herokuapp.com/v1/fortunes?limit=1000&skip=&page=")
			i = random.randint(0,100)
			r = r.json()
			send(room, r[i]['message'])

		if b.startswith("!horoscope "):
			sign = b[11:].strip("\n")
			r = requests.get("http://sandipbgt.com/theastrologer/api/horoscope/{}/today/".format(sign))
			r = r.json()
			horo, _ = r['horoscope'].split("(c)", 1)
			mood = r['meta']['mood']
			kw = r['meta']['keywords']
			send(room, horo)
			send(room, "your mood: {}".format(mood))
			send(room, "you are feeling {}".format(kw))
			
		if b=="!iching\n":
			num = random.randint(1,64)
			url = "http://reoxy.org/iching/{}.html"
			r = requests.get(url.format(num))
			html = BeautifulSoup(r.text)
			name = html.title.text[10:]
			char = unichr(19903+num)		
			send(room, u"{} - {} {}".format(char, name, url.format(num)))

		if b=="!joke\n":
			r = requests.get("https://08ad1pao69.execute-api.us-east-1.amazonaws.com/dev/random_ten")
			r = r.json()
			while 1:
				joke = random.choice(r)
				if joke['type'] == 'general':
					break
			send(room, joke['setup'])
			time.sleep(5)
			send(room, joke['punchline'])

		if b=="!trump\n":
			r = requests.get("https://api.tronalddump.io/random/quote")
			r = r.json()
			send(room, r['value'])

		if b.startswith("!gif "):
			query = b[5:].strip("\n")
			r = requests.get("https://api.gfycat.com/v1/gfycats/search?search_text={}".format(query))
			r = r.json()
			gfy = random.choice(r['gfycats'])
			send(room, gfy['title'])
			send(room, gfy['webpUrl'])

	except Exception:
		print sys.exc_info()[0]
		print "i broke\n"
		print traceback.print_exc()

###############  INIT  ###############

#### TESTBOX ####
r = requests.get("http://fortunecookieapi.herokuapp.com/v1/fortunes?limit=1000&skip=&page=")
i = random.randint(0,100)
r = r.json()
print r[i]['message']
#### TESTBOX ####

#join star fish
subprocess.call('museekcontrol -j "star fish"', shell=True)

#init news api
newsapi = NewsApiClient(api_key='ee4bdf6214d14b8ba0898739c88ef422')

#twitter integration
CONSUMER_KEY = 'TpTKQgiE9I1Znt5zEJn0hdYys'
CONSUMER_SECRET = 'sz2HiIJR6P2QnTs5PDUCZZZHoMyewQIKE2WvX54n5PeWGoeCgC'
ACCESS_KEY = '908805778185838595-SAjbDJCng7ROWEljbXGQ6iwDq32lig6'
ACCESS_SECRET = 'ECSjYZZYhybxSj7rGZCFIfOTwlbuTBSNkKw8gadmsg5JC'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

#timer = 0
#initial clear of old logs
for line in Pygtail("/home/gray/.museekd/logs/room/mutants"):
	line = line

for line in Pygtail("/home/gray/.museekd/logs/room/star fish"):
	line = line

 
#collect links
# with open('mutants.log','r') as f:
#	 for link in BeautifulSoup(f.read(), parse_only=SoupStrainer('a')): 
#		 if link.has_attr('href'): 
#			 print(link['href'])

last_id_tants = ''
last_id_star = ''

###############  LOOP  ###############


while True:
	for line in Pygtail("/home/gray/.museekd/logs/room/mutants"):
		commands('mutants', line)
	for line in Pygtail("/home/gray/.museekd/logs/room/star fish"):
		commands('star fish', line)
	time.sleep(1)
#	timer += 1
#	if timer == 300:
#		send('mutants', 'https://www.youtube.com/watch?v=bOHxtOLfvIo')
#		send('mutants', 'Hoobastank - Crawling In The Dark')
#		timer = 0


	#TODO
	#check for 'None' on !art year
	#intestinate
	#link aggregator
	#split on ' ' and check each word for http, then send to video_id
	#corporae
	#get commands thru pm
	#twitter search
	#youtube search
	#set up files in sane directories
	#number before ! to repeat commands
