#!/usr/bin/env python

"""

This script scrapes URLs from posts and tweets. See /doc/URLs.txt for information on how it works and how it stores data between runs.
At a high level, it begins by injesting all specified posts/tweets, and identifies the links therein.
Any that have already been scraped are ignored. We may eventually need a system for fixing bad results.
Any that have not been scraped are called with the requests module. For successful calls, we log ALL URLs traversed (just in case we need them).
We also dump request text to a file named using an MD5 hash of the final URL minus any query string.

Note that this script contains little inline configuration. URL scraping takes a while because we need to add delays so as to not cause 54 errors.
The best solution is to parallelize execution. But parallelization in this script is a pain, so just do it by running the script several times simultaneously.

To run, execute with the following parameters:
	python scrapeUrls.py [network] [username] [delay]
Parameters:
	* network: one of 'facebook' or 'twitter'
	* username: account/screen name for the given network
	* delay: delay in seconds to wait before retrieving subsequent URLs

The last parameter is complicated. Some hosts are fine with 1 or two seconds delay (e.g., nytimes). Others need 4+ seconds (cnn).
Setting this value is more art than science, so good luck.

"""

##### Configuration

# This script is going to take a long time to run, so we want to store URLs in chunks in case anything goes wrong.
incrementalUrlsToStore = 25



##### Main Setup

# Libraries.
import datetime as dt
import json
from hashlib import md5
import numpy as np
import os
import requests
import shutil
import sys
import time
from urlparse import urlparse

# Data directories.
dirPath_consolidated = '../../../data/%s/consolidated/'
filePath_urls = '../../../data/urls/%s/%s.json'
dirPath_content = '../../../data/content/%s/%s/'
dirPath_urlBackups = '../../../data/backup/urls/%s/'

# Current timestamp.
currTimestamp = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')



##### Configure Source

# TODO: CHECK/VALIDATE PARAMETERS
# Will already fail if insufficient parameters or if they don't follow correct types.

# Set network, screen name, and sleep time based on inputs in sys.argv.
network = str(sys.argv[1])
sn = str(sys.argv[2])
sleepSeconds = int(sys.argv[3])



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

# Validation.
if network not in ['facebook','twitter']:
	print 'Network "%s" invalid; skipping user %s.' % (network, sn)
	quit()

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
# enumerate() pattern is for debugging. It allows us to break after a certain number of posts if necessary.
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
		except requests.exceptions.TooManyRedirects, e:
			# Some links show too many redirects.
			# We don't have any way to denote those now so that we don't check again.
			# Just skip them for now.
			print 'Request for URL "%s" caused an "too many redirects" error:' % url
			print '\t',e
			print 'Skipping.'
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

# Store any last URLs for this user.
json.dump(urls, open(snUrlsFilename,'w'))

# Status.
print 'Finished scrape for %s user @%s.' % (network.title(), sn)
print 'URLs skipped:        %d' % urlsSkipped
print 'URLs retrieved:      %d' % urlsRetrieved
print '      Facebook:      %d' % fbUrlsRetrieved
print '       Twitter:      %d' % twUrlsRetrieved
print 'Posts without a URL: %d' % postsSansUrl
