#!/usr/bin/env python

"""

This script will output statistics about consolidated Facebook posts.
Note that post IDs are string-based and may not be properly interpreted as ordered.

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
consolidatedPostsDirectory = '../../../data/facebook/consolidated/'

# Organization setup.
allOrgs = json.load(open('../../conf/organizations.json'))
if (type(orgs) == type('str')):
	orgs = allOrgs.keys()
relevantOrgs = dict((k, allOrgs[k]) for k in orgs);



##### Get Posts

# General stats about all posts.
totalPosts = 0
minMaxPostDate = None
maxMaxPostDate = None
minMinPostDate = None
maxMinPostDate = None

# Iterate over organizations.
for org, orgData in relevantOrgs.iteritems():
	# Get SN.
	acct = orgData['facebook']

	print '\n%s (@%s):' % (org,acct)

	# Get consolidated post files; get the most recent (file -1).
	postFile = consolidatedPostsDirectory + [f for f in os.listdir(consolidatedPostsDirectory) if f.find(org) == 0 and f[-5:] == '.json'][-1]

	# Load posts.
	posts = json.load(open(postFile))

	# Initialize stat containers.
	maxPostDate = None
	minPostDate = None
	# maxPostId = None
	# minPostId = None

	for post in posts:
		# Save fields we're interested in.
		postDate = dateutil.parser.parse(post['created_time'])
		postId = post['id']
		# Calculate date stats.
		minPostDate = min([d for d in [minPostDate, postDate] if d is not None])
		maxPostDate = max([d for d in [maxPostDate, postDate] if d is not None])
		# Calculate ID stats.
		# minPostId = min([i for i in [minPostId, postId] if i is not None])
		# maxPostId = max([i for i in [maxPostId, postId] if i is not None])

	# Output
	print '\tPost count: %d' % len(posts)
	print '\tMax Date: %s' % str(maxPostDate)
	print '\tMin Date: %s' % str(minPostDate)
	# print '\tMax Post ID: %s' % maxPostId
	# print '\tMin Post ID: %s' % minPostId

	# Update general statistics.
	# Posts.
	totalPosts += len(posts)
	# Max dates.
	minMaxPostDate = min([d for d in [minMaxPostDate, maxPostDate] if d is not None])
	maxMaxPostDate = max([d for d in [maxMaxPostDate, maxPostDate] if d is not None])
	# Min dates.
	minMinPostDate = min([d for d in [minMinPostDate, minPostDate] if d is not None])
	maxMinPostDate = max([d for d in [maxMinPostDate, minPostDate] if d is not None])

# General stats if we've examined more than one account.
if len(relevantOrgs) > 1:
	print '\nOverall Statistics:'
	print '\tPost count: %d' % totalPosts
	print '\tMax Dates:'
	print '\t\tMin(Max Date): %s' % str(minMaxPostDate)
	print '\t\tMax(Max Date): %s' % str(maxMaxPostDate)
	print '\tMin Dates:'
	print '\t\tMin(Min Date): %s' % str(minMinPostDate)
	print '\t\tMax(Min Date): %s' % str(maxMinPostDate)