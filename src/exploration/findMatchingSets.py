#!/usr/bin/env python

"""

This script will find sets of Facebook posts and tweets that appear to be related.

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Matching arrays of screen names.
fbScreenNames = ['nytimes','cnn','huffingtonpost']
twScreenNames = ['nytimes','cnn','huffingtonpost']

# Sets of terms to look for.
keywords = ['Swift','Cuomo','Bradlee']



##### Main Setup

# Libraries.
import json
import os

# Data directory.
consolidatedFbDirectory = '../../../data/facebook/consolidated/'
consolidatedTwDirectory = '../../../data/twitter/consolidated/'

# Output directory.
outputDirectory = '../../../data/exploration/matching/'

# Get Facebook files.
fbFiles = []
twFiles = []
for s in fbScreenNames:
	fbFiles.append(consolidatedFbDirectory + s + '/' + os.listdir(consolidatedFbDirectory + s)[-1])
for s in twScreenNames:
	twFiles.append(consolidatedTwDirectory + s + '/' + os.listdir(consolidatedTwDirectory + s)[-1])

# Containers for content.
fbPosts = []
tweets  = []



##### Get Posts

# Facebook files.
for f in fbFiles:
	# Get posts.
	posts = json.load(open(f))
	# Iterate over all posts.
	for p in posts:
		if 'message' in p.keys() and any(k in p['message'] for k in keywords):
			fbPosts.append(p)

# Twitter files.
for f in twFiles:
	# Get posts.
	posts = json.load(open(f))
	# Iterate over all posts.
	for p in posts:
		if 'text' in p.keys() and any(k in p['text'] for k in keywords):
			tweets.append(p)



##### Output.

# File output.
json.dump(tweets,open(outputDirectory+'tweets.json','w'),indent=4)
json.dump(fbPosts,open(outputDirectory+'fbPosts.json','w'),indent=4)

# Stats.
print 'Facebook posts found:  %d' % len(fbPosts)
print 'Tweets found:         %d' % len(tweets)
