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
	* network: one of 'facebook' or 'twitter'
	* username: account/screen name for the given network
	* delay: delay in seconds to wait before retrieving subsequent URLs
	* scrapeContent: 1 to scrape content, 0 to stop before making any request to the final link destination

The last parameter is complicated. Some hosts are fine with 1 or two seconds delay (e.g., nytimes). Others need 4+ seconds (cnn).
Setting this value is more art than science, so good luck.

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
scrapeContent = True if int(sys.argv[4]) else 0

# Handle target domains for non-scraping.
if not scrapeContent:
	nonScrapingData = json.load(open('../../conf/urlTargetDomains.json'))[sn]
	targetDomain = nonScrapingData['target']
	targetWhitelist = nonScrapingData['whitelist']



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

"""
Traverse URLs until encountering a target domain.
We may want to do this if a site makes an effort to counter scraping or raises "connection reset" errors.

Returns two values: final request object, an error string, and listing of traversed URLs.
If it encounters targetDomain, the final request object will be None. Otherwise, it will contain the final request.
If any request errors, the error's string representation will be passed back.
"""
def traverseUrls(firstUrl,targetDomain,targetWhitelist):
	# Keep track of history.
	hist = [];
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
		# If the destination url is our target, return the list leading up to it.
		if targetDomain is not None and (urlParsed.netloc == targetDomain or urlParsed.netloc[-len(targetDomain)-1:] == '.' + targetDomain) and urlParsed.netloc != targetWhitelist:
			break
		# If it is not, request the URL without redirects.
		try:
			singleRequest = requests.head(nextUrl, allow_redirects=False, timeout=timeoutSeconds)
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

		# Container for URL data. How we fill it depends on scrapeContent.
		urlData = dict()
		# Handle base content cases so we don't need to set "defaults" everywhere.
		urlData['errorText'] = None
		urlData['history'] = []
		urlData['statusCode'] = None
		urlData['scraped'] = False
		content = None

		if scrapeContent:
			# We will scrape content. Just use a regular request.get() call; we don't need to worry about stopping before the end.
			# Make request.
			try:
				# Make request.
				urlRequest = requests.get(url, timeout=timeoutSeconds)
				# Now we have our data. Gather information about the URL(s) themselves.
				# Lots of this could be derived later but storing it will make for easier searching.
				urlData['history'] = [h.url for h in urlRequest.history] + [urlRequest.url]
				# Log status codes. We may use these to detect non-200 results later for diagnostics.
				urlData['statusCode'] = urlRequest.status_code
				# Note that we scraped.
				urlData['scraped'] = True
				# Save content.
				content = urlRequest.text.encode('utf8')
			except:
				urlData['history'] = [url]
				# Get any errors. Alter the object accordingly.
				e = sys.exc_info()[0]
				urlData['errorText'] = str(e)
		else:
			# We are not scraping content. Use a traverseUrls() call in order to avoid triggering a "connection reset" error.
			# Get history.
			finalRequest, errorText, urlsTraversed = traverseUrls(url,targetDomain,targetWhitelist)
			urlData['history'] = urlsTraversed

			# Special behavior if we encountered any content. Note status code.
			if finalRequest is not None:
				urlData['statusCode'] = finalRequest.status_code
			# Handle any errors.
			if errorText is not None:
				urlData['errorText'] = errorText

		# Store MD5.
		urlMd5 = md5(url.encode('utf8')).hexdigest()
		urlData['md5'] = urlMd5

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

		# Save content if we have it.
		if content is not None:
			with open(contentDirectory+urlMd5+'.html','w') as f:
				f.write(content)
			urlsScraped += 1

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
print 'URLs scraped:        %d' % urlsScraped
print 'Posts without a URL: %d' % postsSansUrl
