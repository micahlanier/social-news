#!/usr/bin/env python

"""

This script will consolidate raw tweet files into one large JSON file (timestamped by runtime).

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Organizations to consolidate. Either a list or "all".
orgs = 'all'



##### Main Setup

# Libraries.
import datetime as dt
import dateutil.parser
import json
import os

# Data directory.
rawTweetsDirectory = '../../../data/twitter/raw/'
consolidatedTweetsDirectory = '../../../data/twitter/consolidated/'
# Get timestamp of current run.
timestampFilename = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

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

	print '\nConsolidating tweets for organization "%s" (@%s).' % (org,sn)

	# We're going to hold tweets in one dict.
	# If we end up with a lot of them we may need to be more careful here.
	consolidatedTweets = dict()

	# Keep track of tweets read; min/max date.
	tweetsRead = 0
	minTweetDate = None
	maxTweetDate = None

	# Get list of files. Remove junk in the process.
	rawTweetsFiles = [rtf for rtf in os.listdir(rawTweetsDirectory + org + '/') if rtf[-5:] == '.json']
	# Print status.
	print 'Files found: %d' % len(rawTweetsFiles)

	# Iterate over files.
	for rawTweetFile in rawTweetsFiles:
		# Read in JSON.
		filepath = rawTweetsDirectory + org + '/' + rawTweetFile
		rawTweets = json.load(open(filepath))
		# Iterate over tweets.
		for rawTweet in rawTweets:
			# Get tweet and use it as key for insertion into consolidatedTweets.
			tId = rawTweet['id']
			consolidatedTweets[tId] = rawTweet
			# Track tweet date info.
			currentTweetDate = dateutil.parser.parse(rawTweet['created_at'])
			minTweetDate = min([tDate for tDate in [minTweetDate, currentTweetDate] if tDate is not None])
			maxTweetDate = max([tDate for tDate in [maxTweetDate, currentTweetDate] if tDate is not None])
		# Keep track of tweets read.
		tweetsRead += len(rawTweets)

	# Dump to file.
	filename = consolidatedTweetsDirectory + '/' + org + '-' + timestampFilename + '.json'
	json.dump(consolidatedTweets.values(), open(filename,'w'))

	# Status.
	print 'Done consolidating tweets for organization "%s" (@%s).' % (org,sn)
	print 'Read %d tweets total.' % tweetsRead
	print 'Consolidated to %d tweets.' % len(consolidatedTweets)
	print 'Dates: %s to %s' % (str(minTweetDate),str(maxTweetDate))
