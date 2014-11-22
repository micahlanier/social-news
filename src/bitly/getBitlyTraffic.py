#!/usr/bin/env python

"""

TODO

"""

##### Configuration

# This script is going to take a long time to run, so we want to store URLs in chunks in case anything goes wrong.
incrementalUrlsToStore = 50

# Timeout for hanging URLs.
timeoutSeconds = 10.0



##### Main Setup

# Libraries.
import datetime as dt
import json
import os
import requests
import shutil
import sys
import time
import urllib
from urlparse import urlparse

# Data directories.
filePath_urls = '../../../data/urls/%s/%s.json'
filePath_bitly = '../../../data/bitly/%s/%s.json'
dirPath_bitlyBackups = '../../../data/backup/bitly/%s/'

# Current timestamp.
currTimestamp = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')



##### Main Configuration

# TODO: CHECK/VALIDATE PARAMETERS
# Will already fail if insufficient parameters or if they don't follow correct types.

# Set network, screen name, and sleep time based on inputs in sys.argv.
org = str(sys.argv[1])
network = str(sys.argv[2])
sleepSeconds = float(sys.argv[3])

# Get organizational information.
allOrgs = json.load(open('../../conf/organizations.json'))

# Get organization information for reference.
orgName = allOrgs[org]['name']
bitlyUrl = allOrgs[org]['urls']['bitly']
bitlyUrls = [bitlyUrl,'bit.ly']

# API setup.
bitlySettings = json.load(open('../../../conf/bitly.json'))
bitlyAccessToken = bitlySettings['accessToken']
bitlyClicksBaseUrl = 'https://api-ssl.bitly.com/v3/link/clicks?'



##### Get Traffic

# Statistics.
urlsSkipped = 0
urlsSansBitlyUrl = 0
bitlyStatsRetrieved = 0

# Validation.
if network not in ['facebook','twitter']:
	print 'Network "%s" invalid; skipping %s.' % (network, org)
	quit()

# Status.
print 'Beginning bitly retrieval for %s on %s.' % (orgName, network.title())

# Look for existing Bitly data.
orgBitlyFilename = (filePath_bitly % (network,org))
bitlyFileExists = os.path.exists(orgBitlyFilename)
# Create a Bitly dict if we don't find it.
bitly = dict()
if bitlyFileExists:
	# Bitly file exists. Load it.
	bitly = json.load(open(orgBitlyFilename))

	# Because we're going to be modifying it, create a backup.
	backupFilename = (dirPath_bitlyBackups % network) + org + '-' + currTimestamp + '.json'
	shutil.copyfile(orgBitlyFilename, backupFilename)
	print 'Backed up bitly file to %s' % '/'.join(backupFilename.split('/')[-2:])

# Get URLs.
urls = json.load(open(filePath_urls % (network, org)))

# Traverse all URLs.
# enumerate() pattern is for debugging. It allows us to break after a certain number of URLs if necessary.
for (i, url) in enumerate(urls.keys()):
	# Parse URL to determine if we should read.
	urlInfo = urlparse(url)
	# Examine domain. Ensure a bitly link; else continue.
	if (urlInfo.netloc not in bitlyUrls):
		urlsSansBitlyUrl += 1
		continue
	# Any URL at this point is readable against bitly.

	# Ensure that we haven't already retrieved the URL.
	# TODO: We will want to add capability to go back to certain dates later.
	if (url in bitly):
		urlsSkipped += 1
		continue

	# Okay, now we know that we want to retrieve URL stats.
	# Construct our API call URL.
	requestQsParams = {
		'access_token': bitlyAccessToken,
		'link': urllib.quote(url)
	}
	requestUrl = bitlyClicksBaseUrl + '&'.join([k+'='+v for (k,v) in requestQsParams.iteritems()])

	# Make our request.
	bitlyRequest = requests.get(requestUrl)
	# Convert to dict.
	bitlyRequestData = json.loads(bitlyRequest.text)
	# Append a timestamp for our request.
	bitlyRequestData['retrieved'] = bitlyRequest.headers['date']

	# Store in main bitly container.
	bitly[url] = bitlyRequestData

	# Update statistics.
	bitlyStatsRetrieved += 1

	# Dump data if we've gotten to that point.
	if bitlyStatsRetrieved % incrementalUrlsToStore == 0:
		print 'Storing %d URLs.' % incrementalUrlsToStore
		json.dump(bitly, open(orgBitlyFilename,'w'))

	# Wait, if we want to.
	time.sleep(sleepSeconds)


# Store any last link stats for this user.
json.dump(bitly, open(orgBitlyFilename,'w'))

# Status.
print 'Finished bitly retrieval for %s on %s.' % (orgName, network.title())
print 'URLs skipped:              %d' % urlsSkipped
print 'URLs retrieved:            %d' % bitlyStatsRetrieved
print 'Posts without a bitly URL: %d' % urlsSansBitlyUrl
