#!/usr/bin/env python

"""

This script will consolidate raw tweet files into one large JSON file (timestamped by runtime).

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.
screenNames   = ['nytimes','cnn']



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
timestampFilename = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S') + '.json'



##### Get Tweets

# Iterate over screen names.
for sn in screenNames:
	print 'Consolidating tweets for @%s.' % sn

	# We're going to hold tweets in one dict.
	# If we end up with a lot of them we may need to be more careful here.
	consolidatedTweets = dict()

	# Keep track of tweets processed; min/max date.
	tweetsProcessed = 0
	minTweetDate = None
	maxTweetDate = None

	# Get list of files. Remove junk in the process.
	rawTweetsFiles = [rtf for rtf in os.listdir(rawTweetsDirectory + sn + '/') if rtf[-5:] == '.json']
	# Print status.
	print 'Files found: %d' % len(rawTweetsFiles)

	# Iterate over files.
	for rawTweetFile in rawTweetsFiles:
		# Read in JSON.
		filepath = rawTweetsDirectory + sn + '/' + rawTweetFile
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

	# Set up folder if it doesn't exist.
	consolidatedSnDirectory = consolidatedTweetsDirectory + sn + '/'
	if not os.path.exists(consolidatedSnDirectory):
		os.makedirs(consolidatedSnDirectory)

	# Dump to file.
	filename = consolidatedSnDirectory + '/' + timestampFilename
	json.dump(consolidatedTweets, open(filename,'w'))

	# Status.
	print 'Done consolidating tweets for @%s.' % sn
	print 'Read %d tweets total.' % len(consolidatedTweets)
	print 'Dates: %s to %s' % (str(minTweetDate),str(maxTweetDate))
