#!/usr/bin/env python

"""

This script will consolidate raw post files into one large JSON file (timestamped by runtime).

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# List of accounts to consolidate or "all" to consolidate all of them.
accounts = 'all' # accounts  = ['nytimes','wsj','washingtonpost','globe','latimes','usatoday']



##### Main Setup

# Libraries.
import datetime as dt
import dateutil.parser
import json
import os

# Data directory.
rawPostsDirectory = '../../../data/facebook/raw/'
consolidatedPostsDirectory = '../../../data/facebook/consolidated/'
# Get timestamp of current run.
timestampFilename = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

# Traverse all accounts if set to do so.
if type(accounts) == type('str'):
	accounts = [acct for acct in os.listdir(rawPostsDirectory) if acct != '.DS_Store']



##### Get Tweets

# Iterate over screen names.
for acct in accounts:
	print 'Consolidating posts for @%s.' % acct

	# We're going to hold posts in one dict.
	# If we end up with a lot of them we may need to be more careful here.
	consolidatedPosts = dict()

	# Keep track of posts read; min/max date.
	postsRead = 0
	minPostDate = None
	maxPostDate = None

	# Get list of files. Remove junk in the process.
	rawPostsFiles = [rtf for rtf in os.listdir(rawPostsDirectory + acct + '/') if rtf[-5:] == '.json']
	# Print status.
	print 'Files found: %d' % len(rawPostsFiles)

	# Iterate over files.
	for rawPostFile in rawPostsFiles:
		# Read in JSON.
		filepath = rawPostsDirectory + acct + '/' + rawPostFile
		rawPosts = json.load(open(filepath))
		# Iterate over tweets.
		for rawPost in rawPosts:
			# Get post and use it as key for insertion into consolidatedPosts.
			pId = rawPost['id']
			consolidatedPosts[pId] = rawPost
			# Track tweet date info.
			currentPostDate = dateutil.parser.parse(rawPost['created_time'])
			minPostDate = min([tDate for tDate in [minPostDate, currentPostDate] if tDate is not None])
			maxPostDate = max([tDate for tDate in [maxPostDate, currentPostDate] if tDate is not None])
		# Keep track of posts read.
		postsRead += len(rawPosts)

	# Dump to file.
	filename = consolidatedPostsDirectory + acct + '-' + timestampFilename + '.json'
	json.dump(consolidatedPosts.values(), open(filename,'w'))

	# Status.
	print 'Done consolidating posts for @%s.' % acct
	print 'Read %d posts total.' % postsRead
	print 'Consolidated to %d posts.' % len(consolidatedPosts)
	print 'Dates: %s to %s' % (str(minPostDate),str(maxPostDate))
