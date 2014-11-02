#!/usr/bin/env python

"""

This script will scrape tweets beyond the 3200-tweet limit by scraping the Twitter web search interface.
Expect this process to be slooow.

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# We'll use these libraries immediately.
import dateutil.parser

# Enter a single screen name to scrape.
sn = 'nytimes'
until = dateutil.parser.parse('2014/10/01')



##### Main Setup

# Libraries.
from bs4 import BeautifulSoup
import datetime as dt
import json
import os
# from pytz import timezone
# import pytz
import requests
import time
from twython import Twython

# Ensure "until" setting is comparable to minDate.
# until = pytz.utc.localize(until)
until = until.replace(tzinfo=dateutil.tz.tzutc())

# Data directory.
consolidatedTweetsDirectory = '../../../data/twitter/consolidated/%s/' % sn
if not os.path.exists(consolidatedTweetsDirectory):
	raise Exception('No consolidated tweets for SN @%s.' % sn)

# Data directory.
rawTweetsDirectory = '../../../data/twitter/raw/%s/' % sn
# Get timestamp of current run.
timestampFilename = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S') + '.json'

# Base search URL. Can just append an ID after this.
baseSearchUrl = 'https://twitter.com/search?f=realtime&q=from%%3A%s%%20max_id%%3A' % sn

# Unclear how time zones returned work. But this seems to get us what we're looking for.
# eastern = pytz.timezone('US/Eastern')

# Twitter Setup

# API setup.
apiConfigPath = '../../../conf/twitter.json'
# Read API settings.
twitterSettings = json.load(open(apiConfigPath))
# Set up twitter object.
twitter = Twython(twitterSettings['apiKey'], access_token=twitterSettings['accessToken'])
# Wait time. Ensure we don't run afoul of rate limits.
secondsToWait = 6


### Find Starting Point

# Find all consolidated tweet files and get the most recent.
tweetFile = [f for f in os.listdir(consolidatedTweetsDirectory) if f[-5:] == '.json'][-1]

# Load that file with json.
consolidatedTweets = json.load(open(consolidatedTweetsDirectory+tweetFile))

# Find min ID.
minTweetId = None
for tweet in consolidatedTweets:
	minTweetId = min([tId for tId in [minTweetId, tweet['id']] if tId is not None])

# Status.
print 'Found minimum tweet ID for @%s: %d' % (sn,minTweetId)
print 'Will start search at %d - 1' % minTweetId



### Scraping

# Container for tweets.
tweets = []

# Statistics.
minTweetDate = None
maxTweetDate = None

# Loop terminates with break condition inside once we've found a date.
while True:
	# Decrement ID to avoid repeats.
	minTweetId -= 1

	# Make request and convert to a bs4 object.
	requestUrl = baseSearchUrl + str(minTweetId)
	searchRequest = requests.get(requestUrl)
	soup = BeautifulSoup(searchRequest.text)

	# Traverse all content items and extract tweet data.
	tweetContainers = soup.find_all('div', class_='tweet')

	# Traverse all tweet containers.
	for t in tweetContainers:
		# Find tweet ID for this tweet.
		tweetId = int(t.attrs['data-tweet-id'])

		# Get tweet; append.
		tweet = twitter.show_status(id=tweetId)
		tweets.append(tweet)

		# Get stats.
		minTweetId = minTweetId = min([tId for tId in [minTweetId, tweetId] if tId is not None])
		tweetDate = dateutil.parser.parse(tweet['created_at'])
		minTweetDate = min([tDate for tDate in [minTweetDate, tweetDate] if tDate is not None])
		maxTweetDate = max([tDate for tDate in [maxTweetDate, tweetDate] if tDate is not None])

		# Status.
		print 'Retrieved tweet %d at time %s.' % (tweetId, str(tweetDate))
		print 'Sleeping %d seconds (to avoid API rate limits).' % secondsToWait

		# Wait before making another request.
		time.sleep(secondsToWait)

	# Break if we've gone back far enough.
	if minTweetDate < until:
		break

# Log.
print 'Retrieved %d tweets.' % len(tweets)

# Dump to file.
filename = rawTweetsDirectory + timestampFilename
json.dump(tweets, open(filename,'w'))

# Status.
print 'Done retrieving tweets for @%s.' % sn
print 'Read %d tweets total.' % len(tweets)
print 'Dates: %s to %s' % (str(minTweetDate),str(maxTweetDate))
print 'Oldest ID: %d' % minTweetId
