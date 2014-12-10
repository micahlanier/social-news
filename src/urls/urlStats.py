#!/usr/bin/env python

"""

This script scrapes URLs from posts and tweets. See /doc/URLs.txt for information on how it works and how it stores data between runs.
At a high level, it begins by injesting all specified posts/tweets, and identifies the links therein.
Any that have already been scraped are ignored. We may eventually need a system for fixing bad results.
Any that have not been scraped are called with the requests module. For successful calls, we log ALL URLs traversed (just in case we need them).
We also dump request text to a file named using an MD5 hash of the final URL minus any query string.


"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Specify sources. Any source is a tuple combination of the network (facebook/twitter) and screen name. E.g., ('twitter','nytimes').
sources = [
	('twitter','nytimes')
]

##### Main Setup

# Libraries.
import datetime as dt
import json
import os
import requests
import shutil
from urlparse import urlparse

# Data directories.
dirPath_consolidated = '../../../data/%s/consolidated/'
dirPath_urls = '../../../data/urls/%s/'
dirPath_urlBackups = '../../../data/backup/urls/%s/'

# Current timestamp.
currTimestamp = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')



##### Helper Functions

"""
Return a list of expanded URLs regardless of service.
Automatically exclude some domains: facebook.com, twitter.com. We can 
"""
def associatedUrls(network,post):
	# Get URLs from post data.
	urls = []
	if network == 'facebook' and 'link' in post:
		urls =  [post['link']]
	elif network == 'twitter':
		urls = [u['expanded_url'] for u in post['entities']['urls']]
	# Filter.
	urls = [u for u in urls if not any([d for d in ['facebook.com','twitter.com'] if d in(urlparse(u)).netloc])]
	# Return.
	return urls


##### Get URLs

# Statistics.
urlsAlreadyFound = 0
urlsRetrieved = 0
fbUrlsFound = 0
twUrlsFound = 0

# Traverse all sources.
for (network, sn) in sources:

	# Validation.
	if network not in ['facebook','twitter']:
		print 'Network "%s" invalid; skipping user %s.' % (network, sn)
		break

	# Status.
	print 'Beginning scrape for %s user @%s' % (network.title(), sn)

	# Look for existing URLs.
	urlsFilename = (dirPath_consolidated % network) + sn + '.json'
	fileExists = len([f for f in os.listdir(dirPath_consolidated % network) if f == urlsFilename]) == 1
	# Create a URL dict if we don't find it.
	urls = dict()
	if fileExists:
		# URLs file exists. Load it.
		urls = json.load(open(urlsFilename))
		# Because we're going to be modifying it, create a backup.
		backupFilename = (dirPath_urlBackups % network) + sn + '-' + currTimestamp + '.json'
		shutil.copyfile(urlsFilename, backupFilename)
		print 'Backed up URLs file to %s' % '/'.join(backupFilename.split('/')[-2:])

	# Get posts. Use the latest file if more than one.
	postsFilename = [f for f in os.listdir(dirPath_consolidated % network) if f.find(sn) == 0][-1]
	posts = json.load(open(dirPath_consolidated % network + '/' + postsFilename))

	# Traverse all posts, urls.
	for post in posts:










raise





# Traverse all SNs if set to do so.
if type(screenNames) == type('str'):
	screenNames = [cFile[:cFile.find('-')] for cFile in os.listdir(consolidatedTweetsDirectory) if cFile != '.DS_Store']



##### Get Tweets

# General stats about all posts.
totalTweets = 0
minMaxTweetDate = None
maxMaxTweetDate = None
minMinTweetDate = None
maxMinTweetDate = None

# Iterate over screen names.
for sn in screenNames:
	print '\n@%s:' % sn

	# Get consolidated tweet files; get the most recent (file -1).
	tweetFile = consolidatedTweetsDirectory + [f for f in os.listdir(consolidatedTweetsDirectory) if f.find(sn) == 0 and f[-5:] == '.json'][-1]

	# Load tweets.
	tweets = json.load(open(tweetFile))

	# Initialize stat containers.
	maxTweetDate = None
	minTweetDate = None
	maxTweetId = None
	minTweetId = None

	for tweet in tweets:
		# Save fields we're interested in.
		tweetDate = dateutil.parser.parse(tweet['created_at'])
		tweetId = int(tweet['id'])
		# Calculate date stats.
		minTweetDate = min([d for d in [minTweetDate, tweetDate] if d is not None])
		maxTweetDate = max([d for d in [maxTweetDate, tweetDate] if d is not None])
		# Calculate ID stats.
		minTweetId = min([i for i in [minTweetId, tweetId] if i is not None])
		maxTweetId = max([i for i in [maxTweetId, tweetId] if i is not None])

	# Output
	print '\tMax Date: %s' % str(maxTweetDate)
	print '\tMin Date: %s' % str(minTweetDate)
	print '\tMax Tweet ID: %d' % maxTweetId
	print '\tMin Tweet ID: %d' % minTweetId
	print '\tTweet count: %d' % len(tweets)

	# Update general statistics.
	# Posts.
	totalTweets += len(tweets)
	# Max dates.
	minMaxTweetDate = min([d for d in [minMaxTweetDate, maxTweetDate] if d is not None])
	maxMaxTweetDate = max([d for d in [maxMaxTweetDate, maxTweetDate] if d is not None])
	# Min dates.
	minMinTweetDate = min([d for d in [minMinTweetDate, minTweetDate] if d is not None])
	maxMinTweetDate = max([d for d in [maxMinTweetDate, minTweetDate] if d is not None])


# General stats if we've examined more than one account.
if len(screenNames) > 1:
	print '\nOverall Statistics:'
	print '\tTweet count: %d' % totalTweets
	print '\tMax Dates:'
	print '\t\tMin(Max Date): %s' % str(minMaxTweetDate)
	print '\t\tMax(Max Date): %s' % str(maxMaxTweetDate)
	print '\tMin Dates:'
	print '\t\tMin(Min Date): %s' % str(minMinTweetDate)
	print '\t\tMax(Min Date): %s' % str(maxMinTweetDate)
