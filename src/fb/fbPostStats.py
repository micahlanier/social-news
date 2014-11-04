#!/usr/bin/env python

"""

This script will output statistics about consolidated Facebook posts.
Note that post IDs are string-based and may not be properly interpreted as ordered.

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Set to string "all" to summarize all consolidated posts; otherwise, use a list.
accounts = 'all' # accounts = ['nytimes'] 



##### Main Setup

# Libraries.
import dateutil.parser
import json
import os


# Data directory.
consolidatedPostsDirectory = '../../../data/facebook/consolidated/'
# Traverse all accounts if set to do so.
if type(accounts) == type('str'):
	accounts = [sn for sn in os.listdir(consolidatedPostsDirectory) if sn != '.DS_Store']



##### Get Posts

# General stats about all posts.
totalPosts = 0
minMaxPostDate = None
maxMaxPostDate = None
minMinPostDate = None
maxMinPostDate = None

# Iterate over accounts.
for acct in accounts:
	print '\n@%s:' % acct

	# Get consolidated post files; get the most recent (file -1).
	postFile = consolidatedPostsDirectory + acct + '/' + [f for f in os.listdir(consolidatedPostsDirectory + '/' + acct) if f[-5:] == '.json'][-1]

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
		minPostDate = min([tDate for tDate in [minPostDate, postDate] if tDate is not None])
		maxPostDate = max([tDate for tDate in [maxPostDate, postDate] if tDate is not None])
		# Calculate ID stats.
		# minPostId = min([pId for pId in [minPostId, postId] if pId is not None])
		# maxPostId = max([pId for pId in [maxPostId, postId] if pId is not None])

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
if len(accounts) > 1:
	print '\nOverall Statistics:'
	print '\tPost count: %d' % totalPosts
	print '\tMax Dates:'
	print '\t\tMin(Max Date): %s' % str(minMaxPostDate)
	print '\t\tMax(Max Date): %s' % str(maxMaxPostDate)
	print '\tMin Dates:'
	print '\t\tMin(Min Date): %s' % str(minMinPostDate)
	print '\t\tMax(Min Date): %s' % str(maxMinPostDate)