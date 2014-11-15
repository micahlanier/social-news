#!/usr/bin/env python

"""

This script will pull as many recent tweets as possible from given organizations and dump them to a timestamped file.
If we pull tweets over time, this will allow us to arrange pulls in order and consolidate them into a master file.

We have encountered rate limit failures around 17 consecutive organizations.
Consider dividing the organization list in two and fetching both halves over time.
If it fails, wait 15 minutes and try again. In the future, we can think about cycling through API keys.

Relevant Twitter API documentation:
	https://dev.twitter.com/rest/reference/get/statuses/user_timeline

"""

##### Configuration

# List of organizations to fetch. Either a list or "all".
orgs = 'all'



##### Main Setup

# Libraries.
import datetime as dt
import dateutil.parser
import json
import os
from twython import Twython

# API setup.
apiConfigPath = '../../../conf/twitter.json'

# Data directory.
rawTweetsDirectory = '../../../data/twitter/raw/'
# Get timestamp of current run.
timestampFilename = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S') + '.json'

# Twitter Setup
# Read API settings.
twitterSettings = json.load(open(apiConfigPath))
# Set up twitter object.
twitter = Twython(twitterSettings['apiKey'], access_token=twitterSettings['accessToken'])
# Default number of tweets to grab per request.
tweetsPerRequest = 200

# Organization setup.
allOrgs = json.load(open('../../conf/organizations.json'))
if (type(orgs) == type('str')):
	orgs = allOrgs.keys()
relevantOrgs = dict((k, allOrgs[k]) for k in orgs);



##### Get Tweets

# Iterate over organizations.
for org, orgData in relevantOrgs.iteritems():
	# Get SN.
	sn = orgData['twitter']

	print 'Retrieving tweets for organization "%s" (@%s).' % (org,sn)

	# Set up container for tweets.
	tweets = []
	# Keep track of min tweet ID; min/max dates.
	minTweetId = None
	minTweetDate = None
	maxTweetDate = None
	# Set up folder if it doesn't exist.
	snDirectory = rawTweetsDirectory + org + '/'
	if not os.path.exists(snDirectory):
		os.makedirs(snDirectory)

	# Start looping and grabbing tweets as we go. Loop will terminate at a break.
	# We just set an arbitrarily high limit in case something goes haywire.
	while len(tweets) < 4000:
		# Get tweets.
		if (minTweetId is None):
			currentTweets = twitter.get_user_timeline(screen_name=sn, count=tweetsPerRequest)
		else:
			currentTweets = twitter.get_user_timeline(screen_name=sn, max_id=minTweetId, count=tweetsPerRequest)
		# If nothing there (we've reached the end), break the loop
		if (not len(currentTweets)):
			break
		# Iterate over tweets and find min ID, min/max date.
		for t in currentTweets:
			minTweetId = min([tId for tId in [minTweetId, t['id']-1] if tId is not None])
			currentTweetDate = dateutil.parser.parse(t['created_at'])
			minTweetDate = min([tDate for tDate in [minTweetDate, currentTweetDate] if tDate is not None])
			maxTweetDate = max([tDate for tDate in [maxTweetDate, currentTweetDate] if tDate is not None])
		# Append to list.
		tweets += currentTweets
		# Log.
		print 'Retrieved %d tweets (%d overall).' % (len(currentTweets), len(tweets))

	# Dump to file.
	filename = rawTweetsDirectory + org + '/' + timestampFilename
	json.dump(tweets, open(filename,'w'))

	# Status.
	print 'Done retrieving tweets for organization "%s" (@%s).' % (org,sn)
	print 'Read %d tweets total.' % len(tweets)
	print 'Dates: %s to %s' % (str(minTweetDate),str(maxTweetDate))
