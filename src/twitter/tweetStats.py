#!/usr/bin/env python

"""

This script will consolidate raw tweet files into one large JSON file (timestamped by runtime).

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Set to string "all" to summarize all consolidated tweets; otherwise, use a list.
screenNames = 'all' # screenNames = ['nytimes'] 



##### Main Setup

# Libraries.
import dateutil.parser
import json
import os


# Data directory.
consolidatedTweetsDirectory = '../../../data/twitter/consolidated/'
# Traverse all SNs if set to do so.
if type(screenNames) == type('str'):
	screenNames = [sn for sn in os.listdir(consolidatedTweetsDirectory) if sn != '.DS_Store']



##### Get Tweets

# Iterate over screen names.
for sn in screenNames:
	print '@%s:' % sn

	# Get consolidated tweet files; get the most recent (file -1).
	tweetFile = consolidatedTweetsDirectory + sn + '/' + [f for f in os.listdir(consolidatedTweetsDirectory + '/' + sn) if f[-5:] == '.json'][-1]

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
		if maxTweetDate == None or tweetDate > maxTweetDate:
			maxTweetDate = tweetDate
		if minTweetDate == None or tweetDate < minTweetDate:
			minTweetDate = tweetDate
		if maxTweetId == None or tweetId > maxTweetId:
			maxTweetId = tweetId
		if minTweetId == None or tweetId < minTweetId:
			minTweetId = tweetId

	# Output
	print '\tMax Date: %s' % str(maxTweetDate)
	print '\tMin Date: %s' % str(minTweetDate)
	print '\tMax Tweet ID: %d' % maxTweetId
	print '\tMin Tweet ID: %d' % minTweetId
	print '\tTweet count: %d' % len(tweets)