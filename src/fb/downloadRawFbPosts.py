#!/usr/bin/env python

"""

This script will pull recent Facebook posts from given usernames and dump them to a timestamped file.
If we pull posts over time, this will allow us to arrange pulls in order and consolidate them into a master file.

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# We'll use these libraries immediately.
import datetime as dt
import dateutil.parser

# List of organizations to fetch. Either a list or "all".
orgs = 'all'
# Upper limit of date.
maxDate = dt.datetime(2014,11,10,tzinfo=dateutil.tz.tzutc()) #dt.datetime.utcnow()
# Lower limit of date.
minDate = dt.datetime(2014,10,30,tzinfo=dateutil.tz.tzutc())
# Facebook is not as explicit as Twitter about limiting. Set this as needed if you run into any issues.
postLimit = 75



##### Main Setup

# Libraries.
import json
import os
import requests
import urllib
import time

# API setup.
apiConfigPath = '../../../conf/facebook.json'

# Data directory.
rawPostsDirectory = '../../../data/facebook/raw/'
# Get timestamp of current run.
timestampFilename = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S') + '.json'

# Facebook Setup
# Read API settings.
fbSettings = json.load(open(apiConfigPath))

# Ensure maxDate comparable to minDate.
maxDate = maxDate.replace(tzinfo=dateutil.tz.tzutc())

# Keep a one-second time delta handy for upper-bound limits.
oneSecond = dt.timedelta(seconds=1)

# Sleep interval for transient errors.
sleepTimeSeconds = 4

# Organization setup.
allOrgs = json.load(open('../../conf/organizations.json'))
if (type(orgs) == type('str')):
	orgs = allOrgs.keys()
relevantOrgs = dict((k, allOrgs[k]) for k in orgs)




##### Facebook Helper Code

"""
Simple function for performing a Facebook GET request.
Does not check parameters, so be careful!
"""
def facebookGet(path, accessToken, parameters, version = '2.1'):
	fbUrl = 'https://graph.facebook.com/v' + version + '/'
	# Add request path.
	fbUrl += path.strip('/') + '/'
	# Add access token.
	fbUrl += '?access_token=' + accessToken
	# Add additional parameters.
	for pKey, pValue in parameters.iteritems():
		fbUrl += '&%s=%s' % (pKey, urllib.quote(str(pValue)))
	return requests.get(fbUrl)



##### Get Facebook Posts

# Iterate over organizations.
for org, orgData in relevantOrgs.iteritems():
	# Get account.
	acct = orgData['facebook']

	print 'Retrieving posts for organization "%s" (@%s).' % (org,acct)

	# Set up folder if it doesn't exist.
	acctDirectory = rawPostsDirectory + org + '/'
	if not os.path.exists(acctDirectory):
		os.makedirs(acctDirectory)

	# Set up container for posts.
	posts = []

	# Set up a loop date.
	loopMaxDate = maxDate

	# Set up objects hold our request.
	requestPath = acct + '/feed'
	requestParams = dict()
	requestParams['limit'] = postLimit

	# Don't bother with getting ALL comments/likes. We're only interested in summary statistics.
	# While it would be cool to analyze all of the people who comment/like, that's a PITA in the time we have.
	# By doing this, we need to specify a whitelist of all fields that we want.
	apiFields = [
		'comments.limit(1).summary(true)','likes.limit(1).summary(true)',
		'caption','created_time','description','from','id','link','message','name','shares','status_type','type'
	]
	requestParams['fields'] = ','.join(apiFields)

	# Reload settings just in case we've changed access tokens and are running manually.
	fbSettings = json.load(open(apiConfigPath))

	# Loop until we have gone back to minDate.
	while loopMaxDate > minDate:
		# Compose a request with the latest max date.
		requestParams['until'] = str(loopMaxDate)
		# Make request; parse JSON.
		facebookRequest = facebookGet(requestPath, fbSettings['accessToken'], requestParams)
		jsonFacebookRequest = json.loads(facebookRequest.text)

		# Detect any errors.
		if 'error' in jsonFacebookRequest:
			if jsonFacebookRequest['error']['code'] == 2:
				# Tranient, "unexpected" error. Sleep for a sec and then continue.
				print 'Unexpected error. Sleeping %d seconds.' % sleepTimeSeconds
				time.sleep(2)
				continue
			else:
				print 'Encountered a major error. Breaking loop.'
				print jsonFacebookRequest['error']
				break

		# If no errors, we got data.
		currentPosts = jsonFacebookRequest['data']

		# Break if we didn't get anything; otherwise append and continue.
		if (not len(currentPosts)):
			break
		posts += currentPosts

		# Get date for next request. Go back one second, because for some reason they use inclusive logic.
		loopMaxDate = dateutil.parser.parse(currentPosts[-1]['created_time']) - oneSecond

		# Status.
		print 'Retrieved %d posts (%d overall).' % (len(currentPosts), len(posts))
		print 'Reached date %s.' % str(loopMaxDate + oneSecond)

	# Dump to file.
	filename = acctDirectory + timestampFilename
	json.dump(posts, open(filename,'w'), indent=0)

	# Get max/min dates retrieved.
	minDateRetrieved = loopMaxDate + oneSecond
	maxDateRetrieved = dateutil.parser.parse(posts[0]['created_time'])

	# Status.
	print 'Done retrieving posts for "%s" (@%s).' % (org,acct)
	print 'Read %d posts total.' % len(posts)
	print 'Dates: %s to %s' % (str(minDateRetrieved),str(maxDateRetrieved))
	print 'Wrote output to: %s' % filename
