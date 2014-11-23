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
	python scrapeUrls.py [network] [username] [delay] [scrapeContent]
Parameters:
	* organization: organization name for the given network
	* network: one of 'facebook' or 'twitter'
	* delay: delay in seconds to wait before retrieving subsequent URLs
	* scrapeContent: 1 to scrape content, 0 to stop before making any request to the final link destination

Scraping is complicated. Some hosts are fine with 1 or two seconds delay (e.g., nytimes). Others need 4+ seconds (cnn).
Setting delays for this is more art than science, so good luck.

"""

##### Configuration

# This script is going to take a long time to run, so we want to store URLs in chunks in case anything goes wrong.
incrementalUrlsToStore = 25

# Timeout for hanging URLs.
timeoutSeconds = 10.0



##### Main Setup

# Libraries.
import datetime as dt
import json
from hashlib import md5
import numpy as np
import os
import re
import requests
import shutil
import sys
import time
from urlparse import urlparse

# Our own custom URL parsing code for Facebook.
import socialUrlUtils

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
org = str(sys.argv[1])
network = str(sys.argv[2])
sleepSeconds = int(sys.argv[3])
scrapeContent = True if int(sys.argv[4]) else 0

# Get organizational information.
allOrgs = json.load(open('../../conf/organizations.json'))

# Get information about the organization's URLs.
targetDomain = allOrgs[org]['urls']['domain']
bitlyUrl = allOrgs[org]['urls']['bitly']
stillTraversePattern = allOrgs[org]['urls']['stillTraverse'] if 'stillTraverse' in allOrgs[org]['urls'] else None

# Any other miscellanea.
orgName = allOrgs[org]['name']



##### Helper Functions

"""
Return a list of expanded URLs regardless of service. Don't do any cleaning of URLs.
"""
def associatedUrls(network,post):
	if network == 'facebook':
		links = []
		if 'link' in post:
			links += [post['link']]
		if 'message' in post:
			links += socialUrlUtils.urlsInText(post['message'])
		return links
	elif network == 'twitter':
		return [u['expanded_url'] for u in post['entities']['urls']]
	return []

"""
Traverse URLs until encountering a target domain.
We may want to do this if a site makes an effort to counter scraping or raises "connection reset" errors.

Returns two values: final request object, an error string, and listing of traversed URLs.
If it encounters targetDomain, the final request object will be None. Otherwise, it will contain the final request.
If any request errors, the error's string representation will be passed back.
"""
def traverseUrls(firstUrl, targetDomain, stillTraversePattern, bitlyUrl, scrape=False):
	# Keep track of history.
	hist = []
	# Other return objects to keep.
	errorText = None
	lastRequest = None

	# Keep looping until we no longer have a URL to traverse.
	# We may manually break the loop inside if we want to exit immediately.
	nextUrl = firstUrl
	while nextUrl is not None:
		# Append the URL to history.
		hist += [nextUrl]
		# Parse URL.
		urlParsed = urlparse(nextUrl)
		# If the destination url is our target and we're not scraping, return the list leading up to it.
		# We test a LOT of conditions here. Break and return if the following is true:
		# 	The domain is indeed the "target" domain (e.g., nytimes.com).
		# 	The domain is not part of a bitly link (handles cases like the on.wsj.com bitly domain).
		#	The domain does not match an internal redirection page (handles cases like http://www.theguardian.com/p/3p6jv/tw).
		if (
				not scrape
			and	targetDomain is not None and (urlParsed.netloc == targetDomain or urlParsed.netloc[-len(targetDomain)-1:] == '.' + targetDomain)
			and urlParsed.netloc != bitlyUrl
			and (stillTraversePattern is None or not re.match(stillTraversePattern,nextUrl))
		):
			break
		# If it is not, request the URL without redirects.
		# Use a get request if scraping.
		try:
			if (not scrape) or urlParsed.netloc in [bitlyUrl,'bit.ly','trib.al']:
				singleRequest = requests.head(nextUrl, allow_redirects=False, timeout=timeoutSeconds)
			else:
				singleRequest = requests.get(nextUrl, allow_redirects=False, timeout=timeoutSeconds)
		except:
			# We can experience connection errors for various reasons.
			# If we encounter one, append the URL to the end and move on.
			e = sys.exc_info()[0]
			errorText = str(e)
			break
		# We have a request. Look for a location in the header. If none, we've reached the end and can return.
		if 'location' not in singleRequest.headers:
			# Store our request as the last request.
			lastRequest = singleRequest
			break
		# Set the next URL to traverse.
		nextUrl = singleRequest.headers['location']
		# To avoid loops, verify if address has been traversed before.
		if nextUrl in hist:
			errorText = 'Loop encountered'
			break
		
	# Return.
	return lastRequest, errorText, hist




##### Get URLs

# Statistics.
urlsSkipped = 0
urlsRetrieved = 0
fbUrlsRetrieved = 0
twUrlsRetrieved = 0
postsSansUrl = 0
urlsScraped = 0

# Validation.
if network not in ['facebook','twitter']:
	print 'Network "%s" invalid; skipping user %s.' % (network, org)
	quit()

# Status.
print 'Beginning %s URL scrape for %s.' % (network.title(), orgName)

# Look for existing URLs.
orgUrlsFilename = (filePath_urls % (network,org))
urlsFileExists = os.path.exists(orgUrlsFilename)
# Create a URL dict if we don't find it.
urls = dict()
if urlsFileExists:
	# URLs file exists. Load it.
	urls = json.load(open(orgUrlsFilename))

	# Because we're going to be modifying it, create a backup.
	backupFilename = (dirPath_urlBackups % network) + org + '-' + currTimestamp + '.json'
	shutil.copyfile(orgUrlsFilename, backupFilename)
	print 'Backed up URLs file to %s' % '/'.join(backupFilename.split('/')[-2:])

# Get posts. Use the latest file if more than one.
postsFilename = [f for f in os.listdir(dirPath_consolidated % network) if f.find(org) == 0][-1]
posts = json.load(open(dirPath_consolidated % network + '/' + postsFilename))

# Set up content directory path. Create if doesn't exist.
contentDirectory = dirPath_content % (network, org)
if not os.path.exists(contentDirectory):
	os.makedirs(contentDirectory)

# Traverse all posts, urls.
# enumerate() pattern is for debugging. It allows us to break after a certain number of posts if necessary.
# Can remove before release.
for (i, post) in enumerate(posts):
	# Get links and traverse.
	postUrls = associatedUrls(network,post)
	if len(postUrls) == 0:
		postsSansUrl += 1
	for url in postUrls:
		# Check to see if URL has ever been checked before. If so, note it and continue.
		# In practice, this is like breaking (most posts only have one link).
		# But we must continue in case there is another link in the post that is valid.
		if url in urls:
			urlsSkipped += 1
			continue

		# Container for URL data. How we fill it depends on scrapeContent.
		urlData = dict()
		# Handle base content cases so we don't need to set "defaults" everywhere.
		urlData['errorText'] = None
		urlData['history'] = []
		urlData['statusCode'] = None
		urlData['scraped'] = scrapeContent
		content = None

		# Make request. Use a traverseUrl() call to avoid triggering connection resets or contaminating Bitly observations.
		finalRequest, errorText, urlsTraversed = traverseUrls(url,targetDomain,stillTraversePattern,bitlyUrl,scrapeContent)

		# Set up history, status codes. Codes only available if we made a final request.
		urlData['history'] = urlsTraversed
		if finalRequest is not None:
			urlData['statusCode'] = finalRequest.status_code

		# Handle errors.
		if errorText is not None:
			urlData['errorText'] = errorText

		# Store MD5. Used for determining write location of content if we scraped it.
		urlMd5 = md5(url.encode('utf8')).hexdigest()
		urlData['md5'] = urlMd5

		# Save content if we have it.
		if finalRequest is not None and bool(finalRequest.content):
			with open(contentDirectory+urlMd5+'.html','w') as f:
				f.write(finalRequest.content)
			urlsScraped += 1

		# Parse final URL.
		urlParsed = urlparse(urlData['history'][-1])
		urlData['endUrl'] = {
			'url': urlData['history'][-1],
			'scheme': urlParsed.scheme,
			'netloc': urlParsed.netloc,
			'path': urlParsed.path,
			'query': urlParsed.query,
			'fragment': urlParsed.fragment
		}

		# Store in main URLs dictionary.
		urls[url] = urlData

		# Statistics.
		urlsRetrieved += 1
		if (network == 'twitter'):
			twUrlsRetrieved += 1
		else:
			fbUrlsRetrieved += 1

		# Dump URLs if we've gotten to that point.
		if urlsRetrieved % incrementalUrlsToStore == 0:
			print 'Storing %d URLs.' % incrementalUrlsToStore
			json.dump(urls, open(orgUrlsFilename,'w'))

		# Wait, if we want to.
		time.sleep(sleepSeconds)

# Store any last URLs for this user.
json.dump(urls, open(orgUrlsFilename,'w'))

# Status.
print 'Finished scrape for %s user @%s.' % (network.title(), org)
print 'URLs skipped:        %d' % urlsSkipped
print 'URLs retrieved:      %d' % urlsRetrieved
print '      Facebook:      %d' % fbUrlsRetrieved
print '       Twitter:      %d' % twUrlsRetrieved
print 'URLs scraped:        %d' % urlsScraped
print 'Posts without a URL: %d' % postsSansUrl
