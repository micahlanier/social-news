#!/usr/bin/env python

"""

This script outputs statistics about consolidated tweets.

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Organizations for which to generate statistics. Either a list or "all".
orgs = 'all'



##### Main Setup

# Libraries.
import dateutil.parser
import json
import os


# Data directory.
consolidatedTweetsDirectory = '../../../data/twitter/consolidated/'

# Organization setup.
allOrgs = json.load(open('../../conf/organizations.json'))
if (type(orgs) == type('str')):
	orgs = allOrgs.keys()
relevantOrgs = dict((k, allOrgs[k]) for k in orgs);



##### Get Tweets

# General stats about all posts.
totalTweets = 0
minMaxTweetDate = None
maxMaxTweetDate = None
minMinTweetDate = None
maxMinTweetDate = None

# Iterate over organizations.
for org, orgData in relevantOrgs.iteritems():
	# Get SN.
	sn = orgData['twitter']

	print '\n%s (@%s):' % (org,sn)

	# Get consolidated tweet files; get the most recent (file -1).
	tweetFile = consolidatedTweetsDirectory + [f for f in os.listdir(consolidatedTweetsDirectory) if f.find(org) == 0 and f[-5:] == '.json'][-1]

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
if len(relevantOrgs) > 1:
	print '\nOverall Statistics:'
	print '\tTweet count: %d' % totalTweets
	print '\tMax Dates:'
	print '\t\tMin(Max Date): %s' % str(minMaxTweetDate)
	print '\t\tMax(Max Date): %s' % str(maxMaxTweetDate)
	print '\tMin Dates:'
	print '\t\tMin(Min Date): %s' % str(minMinTweetDate)
	print '\t\tMax(Min Date): %s' % str(maxMinTweetDate)
