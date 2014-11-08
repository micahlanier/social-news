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
	('twitter','cnn'),
	('twitter','nytimes'),
	('twitter','abc'),
	('twitter','cbsnews'),
	('twitter','nbcnews')
]

# We probably don't want to make as many calls as possible as quickly as possible. Sleep between requests.
# Some sources need more time. CNN, e.g., seems to like more than 2 seconds.
sleepSeconds = 2

# This script is going to take a long time to run, so we want to store URLs in chunks.
incrementalUrlsToStore = 100

##### Main Setup

# Libraries.
import datetime as dt
import json
from hashlib import md5
import numpy as np
import os
import requests
import shutil
import time
from urlparse import urlparse

# Data directories.
dirPath_consolidated = '../../../data/%s/consolidated/'
filePath_urls = '../../../data/urls/%s/%s.json'
dirPath_content = '../../../data/content/%s/%s/'
dirPath_urlBackups = '../../../data/backup/urls/%s/'

# Current timestamp.
currTimestamp = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')



##### Helper Functions

"""
Return a list of expanded URLs regardless of service. Don't do any cleaning of URLs.
"""
def associatedUrls(network,post):
	if network == 'facebook' and 'link' in post:
		return [post['link']]
	elif network == 'twitter':
		return [u['expanded_url'] for u in post['entities']['urls']]
	return []


##### Get URLs

# Statistics.
urlsSkipped = 0
urlsRetrieved = 0
fbUrlsRetrieved = 0
twUrlsRetrieved = 0
postsSansUrl = 0

# Traverse all sources.
for (network, sn) in sources:

	# Validation.
	if network not in ['facebook','twitter']:
		print 'Network "%s" invalid; skipping user %s.' % (network, sn)
		break

	# Status.
	print 'Beginning scrape for %s user @%s.' % (network.title(), sn)

	# Look for existing URLs.
	snUrlsFilename = (filePath_urls % (network,sn))
	urlsFileExists = os.path.exists(snUrlsFilename)
	# Create a URL dict if we don't find it.
	urls = dict()
	if urlsFileExists:
		# URLs file exists. Load it.
		urls = json.load(open(snUrlsFilename))

		# Because we're going to be modifying it, create a backup.
		backupFilename = (dirPath_urlBackups % network) + sn + '-' + currTimestamp + '.json'
		shutil.copyfile(snUrlsFilename, backupFilename)
		print 'Backed up URLs file to %s' % '/'.join(backupFilename.split('/')[-2:])

	# Get posts. Use the latest file if more than one.
	postsFilename = [f for f in os.listdir(dirPath_consolidated % network) if f.find(sn) == 0][-1]
	posts = json.load(open(dirPath_consolidated % network + '/' + postsFilename))

	# Set up content directory path. Create if doesn't exist.
	contentDirectory = dirPath_content % (network, sn)
	if not os.path.exists(contentDirectory):
		os.makedirs(contentDirectory)

	# Sometimes we encounter severe errors when retrying.
	# It is a pain to break gracefully, so use a boolean to confirm we should keep going.
	criticalError = False

	# Traverse all posts, urls.
	for (i, post) in enumerate(posts):
		# Get links and traverse.
		postUrls = associatedUrls(network,post)
		if len(postUrls) == 0:
			postsSansUrl += 1
		for url in postUrls:
			# Check to see if URL has ever been checked before. If so, note it and break.
			if url in urls:
				urlsSkipped += 1
				break
			# Make request.
			try:
				urlRequest = requests.get(url)
			except requests.exceptions.ConnectionError, e:
				# Fow now, handle severe exceptions by breaking fully.
				print 'Request for URL "%s" caused an error:' % url
				print '\t',e
				print 'Breaking all pulls for @%s.' % sn
				criticalError = True
				break

			# Now we have our data. Gather information about the URL(s) themselves.
			# Lots of this could be derived later but storing it will make for easier searching.
			urlData = dict()
			urlData['history'] = [h.url for h in urlRequest.history] + [urlRequest.url]
			urlMd5 = md5(url).hexdigest()
			urlData['md5'] = urlMd5
			# Store particular things about the end URL.
			urlParsed = urlparse(urlRequest.url)
			urlData['endUrl'] = dict({
				'url': urlRequest.url,
				'scheme': urlParsed.scheme,
				'netloc': urlParsed.netloc,
				'path': urlParsed.path,
				'query': urlParsed.query,
				'fragment': urlParsed.fragment
			})
			# Log status codes. We may use these to detect non-200 results later for diagnostics.
			urlData['statusCode'] = urlRequest.status_code
			# Store in main URLs dictionary.
			urls[url] = urlData

			# Save content to a file.
			with open(contentDirectory+urlMd5+'.html','w') as f:
				f.write(urlRequest.text.encode('utf8'))

			# Statistics.
			urlsRetrieved += 1
			if (network == 'twitter'):
				twUrlsRetrieved += 1
			else:
				fbUrlsRetrieved += 1

			# Dump URLs if we've gotten to that point.
			if urlsRetrieved % incrementalUrlsToStore == 0:
				print 'Storing %d URLs.' % incrementalUrlsToStore
				json.dump(urls, open(snUrlsFilename,'w'))

			# Wait, if we want to.
			time.sleep(sleepSeconds)

		# If we encountered a critical error, break.
		if criticalError:
			break

		##### DEBUGGING
		if i == 1:
			break

	# Store any last URLs for this user.
	json.dump(urls, open(snUrlsFilename,'w'))

	# Status.
	print 'Finished scrape for %s user @%s.' % (network.title(), sn)

# Status information.
print 'Finished all users.'
print 'URLs skipped:        %d' % urlsSkipped
print 'URLs retrieved:      %d' % urlsRetrieved
print '      Facebook:      %d' % fbUrlsRetrieved
print '       Twitter:      %d' % twUrlsRetrieved
print 'Posts without a URL: %d' % postsSansUrl
