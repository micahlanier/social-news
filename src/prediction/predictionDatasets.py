#!/usr/bin/env python

"""

TODO

"""


##### Configuration



##### Main Setup

# Libraries.

from dateutil.parser import parse as dp
import json
from nltk import word_tokenize as tokenize
import os
import pandas as pd
import pytz
import socialUrlUtils

# Data directories.
dirPath_consolidatedTw = '../../../data/twitter/consolidated/'
dirPath_consolidatedFb = '../../../data/facebook/consolidated/'
dirPath_bitly = '../../../data/bitly/%s/'
dirPath_sentiment = '../../../data/sentiment/%s/'
filePath_dates = '../../conf/dates.json'
filePath_output = '../../../data/unmergedPostSummaries/%s.csv'
filePath_users = '../../data/users/%s.json'

# User information.
# usersTw = json.load(open('../../data/users/twitter.json'))
# usersFb = json.load(open('../../data/users/facebook.json'))
# Actually, nevermind. Rely on downstream processes to use these for adjustment.

# Get organizational information.
orgs = json.load(open('../../conf/organizations.json'))

# Get account information.
twAccounts = json.load(open(filePath_users % 'twitter'))
fbAccounts = json.load(open(filePath_users % 'facebook'))

# Tokens to skip for word count.
# This is an inherently difficult task, but this should help us get to where we need to go.
skipTokens = {'\'s','.','?',',','(',')','#','\\',':',';','@','-','\''}

# Facebook status type mapping.
fbStatusTypeToMedium = {'added_photos': 'photo', 'added_video': 'video'}

# Information about proper dates.
dates = json.load(open(filePath_dates))
twStartDate = dp(dates['twitter']['start'])
twEndDate   = dp(dates['twitter']['end'])
fbStartDate  = dp(dates['facebook']['start'])
fbEndDate    = dp(dates['facebook']['end'])

# Get local timezone.
localTz = pytz.timezone('America/New_York')

# URL counts. Allows us to adjust URL traffic.
urlCounts = dict()		# Click counts by URL.
urlNetworks = dict()	# Distinct networks by URL.
retweetedUrls = set()	# Set of all retweets.

# Containers for statistics that will become DFs.
tweetInfo = []
postInfo  = []



##### Helper Functions

"""
Remove URLs, clean syntax.
"""
def cleanMessage(message):
	# Remove Twitter-specific syntax.
	message = message.replace('@','')
	message = message.replace('#','')
	# Remove links.
	links = socialUrlUtils.urlsInText(message)
	# links.reverse()
	for link in links:
		message = message.replace(link,'')
	# Return.
	return message.strip()



##### Main Execution

# Traverse all organizations.
for org, orgData in orgs.iteritems():
	# Org setup.
	orgName = orgData['name']

	# Status.
	print 'Consolidating data for %s.' % orgName

	# Get all relevant Twitter information.
	service   = 'twitter'
	tweets    = json.load(open(dirPath_consolidatedTw + [f for f in os.listdir(dirPath_consolidatedTw) if f.startswith(org)][-1]))
	bitly     = json.load(open((dirPath_bitly % service) + org + '.json'))
	sentiment = json.load(open((dirPath_sentiment % service) + org + '.json'))

	# Traverse tweets.
	for tweet in tweets:
		# Get some initial information.
		expandedUrls = [u['expanded_url'] for u in tweet['entities']['urls']]
		# Ensure date in proper range. We want to exclude everything outside of it.
		created_utc = dp(tweet['created_at'])
		if created_utc < twStartDate or created_utc >= twEndDate:
			continue

		# Container to store stats that will eventually become a data frame.
		thisTweet = { 'service': service, 'id': tweet['id']}

		# Tweet features.
		thisTweet['text'] = tweet['text']
		thisTweet['hashtags'] = len(tweet['entities']['hashtags'])
		thisTweet['retweeted'] = ('retweeted_status' in tweet or tweet['text'].startswith('RT '))
		media = tweet['entities'].get('media')
		thisTweet['medium'] = media[0]['type'] if media else 'text'
		# Tweet datetime features.
		thisTweet['date_utc'] = str(created_utc.date())
		thisTweet['day_of_week_utc'] = created_utc.weekday()
		thisTweet['weekend_utc'] = thisTweet['day_of_week_utc'] >= 5
		thisTweet['time_utc'] = float(created_utc.hour) + float(created_utc.minute)/60
		thisTweet['minute_utc'] = float(created_utc.minute)
		created_est = created_utc.replace(tzinfo=pytz.utc).astimezone(localTz)
		thisTweet['date_est'] = str(created_est.date())
		thisTweet['day_of_week_est'] = created_est.weekday()
		thisTweet['weekend_est'] = thisTweet['day_of_week_est'] >= 5
		thisTweet['time_est'] = float(created_est.hour) + float(created_est.minute)/60
		thisTweet['minute_est'] = float(created_est.minute)
		# Org features.
		thisTweet['org'] = org
		thisTweet['org_category'] = orgData['category'].lower()
		thisTweet['followers_count'] = twAccounts[org]['followers_count']
		# Sentiment features.
		thisTweet['word_count'] = len([t for t in tokenize(cleanMessage(tweet['text'])) if t not in skipTokens])
		sent = sentiment.get(str(tweet['id']))
		if sent:
			thisTweet['sentiment_class'] = sent['class']
			thisTweet['sentiment_score_positive'] = sent['meanScorePosSig']
			thisTweet['sentiment_score_negative'] = sent['meanScoreNegSig']
		else:
			thisTweet['sentiment_class'] = None
			thisTweet['sentiment_score_positive'] = None
			thisTweet['sentiment_score_negative'] = None

		# Tweet outcomes.
		thisTweet['favorites'] = tweet['favorite_count']
		thisTweet['retweets']  = tweet['retweet_count']

		# Bitly features. This is going to be tougher.
		# Traverse all URLs and store those that we've traversed.
		# We'll make a second pass later and clean up.
		thisTweet['raw_clicks'] = dict()
		for u in set(expandedUrls):
			# Increment count in urlCounts.
			urlCounts[u] = (urlCounts.get(u) or 0) + 1
			# Identify retweeted URLs.
			if (thisTweet['retweeted']):
				retweetedUrls.add(u)
			# Identify URL as posted on Twitter.
			if (u not in urlNetworks): urlNetworks[u] = set()
			urlNetworks[u].add(service)
			# Update raw clicks.
			thisTweet['raw_clicks'][u] = bitly[u]['data']['link_clicks'] if u in bitly and bitly[u]['data'] else None

		# Whew. Finally. Now append to the list.
		tweetInfo.append(thisTweet)

	# Get all relevant Facebook information.
	service   = 'facebook'
	posts     = json.load(open(dirPath_consolidatedFb + [f for f in os.listdir(dirPath_consolidatedFb) if f.startswith(org)][-1]))
	bitly     = json.load(open((dirPath_bitly % service) + org + '.json'))
	sentiment = json.load(open((dirPath_sentiment % service) + org + '.json'))

	# Traverse posts.
	for post in posts:
		# Get some initial information.
		expandedUrls = []
		if 'link' in post:
			expandedUrls.append(post['link'])
		if 'message' in post:
			expandedUrls += socialUrlUtils.urlsInText(post['message'])
		created_utc = dp(post['created_time'])
		# Ensure date in proper range. We want to exclude everything outside of it.
		if created_utc < fbStartDate or created_utc >= fbEndDate:
			continue

		# Container to store stats that will eventually become a data frame.
		thisPost = { 'service': service, 'id': post['id']}

		# Post features.
		thisPost['text'] = post.get('message')
		thisPost['medium'] = fbStatusTypeToMedium.get(post.get('status_type')) or 'other'
		# Post datetime features.
		thisPost['date_utc'] = str(created_utc.date())
		thisPost['day_of_week_utc'] = created_utc.weekday()
		thisPost['weekend_utc'] = thisPost['day_of_week_utc'] >= 5
		thisPost['time_utc'] = float(created_utc.hour) + float(created_utc.minute)/60
		thisPost['minute_utc'] = float(created_utc.minute)
		created_est = created_utc.replace(tzinfo=pytz.utc).astimezone(localTz)
		thisPost['date_est'] = str(created_est.date())
		thisPost['day_of_week_est'] = created_est.weekday()
		thisPost['weekend_est'] = thisPost['day_of_week_est'] >= 5
		thisPost['time_est'] = float(created_est.hour) + float(created_est.minute)/60
		thisPost['minute_est'] = float(created_est.minute)
		# Org features.
		thisPost['org'] = org
		thisPost['org_category'] = orgData['category'].lower()
		thisPost['account_likes'] = fbAccounts[org]['likes']
		# Sentiment features.
		thisPost['word_count'] = len([t for t in tokenize(cleanMessage(post['message'])) if t not in skipTokens]) if 'message' in post else 0
		sent = sentiment.get(str(post['id']))
		if sent:
			thisPost['sentiment_class'] = sent['message']['class']
			thisPost['sentiment_score_positive'] = sent['message']['meanScorePosSig']
			thisPost['sentiment_score_negative'] = sent['message']['meanScoreNegSig']
			thisPost['agg_sentiment_class'] = sent['agg']['class']
			thisPost['agg_sentiment_score_positive'] = sent['agg']['meanScorePosSig']
			thisPost['agg_sentiment_score_negative'] = sent['agg']['meanScoreNegSig']
		else:
			thisPost['message_sentiment_class'] = None
			thisPost['message_sentiment_score_positive'] = None
			thisPost['message_sentiment_score_negative'] = None
			thisPost['agg_sentiment_class'] = None
			thisPost['agg_sentiment_score_positive'] = None
			thisPost['agg_sentiment_score_negative'] = None

		# Post outcomes.
		thisPost['comments'] = post['comments']['summary']['total_count'] if 'comments' in post else 0
		thisPost['likes']    = post['likes']['summary']['total_count'] if 'likes' in post else 0
		thisPost['shares']   = post['shares']['count'] if 'shares' in post else 0

		# Bitly features. This is going to be tougher.
		# Traverse all URLs and store those that we've traversed.
		# We'll make a second pass later and clean up.
		thisPost['raw_clicks'] = dict()
		for u in set(expandedUrls):
			# Increment count in urlCounts.
			urlCounts[u] = (urlCounts.get(u) or 0) + 1
			# Identify URL as posted on Twitter.
			if (u not in urlNetworks): urlNetworks[u] = set()
			urlNetworks[u].add(service)
			# Update raw clicks.
			thisPost['raw_clicks'][u] = bitly[u]['data']['link_clicks'] if u in bitly and bitly[u]['data'] else None

		# Whew. Finally. Now append to the list.
		postInfo.append(thisPost)

# Now perform a second pass to calculate the final clicks metric.
# Apply the following rules:
# 	- Retweeted URLs should be nullified.
# 	- Links posted multiple times are assumed to only be included in the observed tweets/posts.
#	  Distribute their clicks among all observations.
#	- Nullify any links posted both to Facbook and Twitter.
# 	  Disaggregation is impossible and they make comparisons dangerous.
# Note that there is always a possibility that a link was posted outside of the observed content. We have no way of knowing.

# Traverse tweets.
for i, tI in enumerate(tweetInfo):
	# There will be lots of nullifications, so treat that as our base case.
	tweetInfo[i]['clicks'] = None
	# Handle retweets.
	if not tI['retweeted']:
		# If not one, traverse all links.
		for u, c in tI['raw_clicks'].iteritems():
			# Do nothing for URLs that have been retweeted, have no click info, or are shared across networks.
			# Otherwise, divide clicks by number of times link posted.
			if c and u not in retweetedUrls and len(urlNetworks[u]) == 1:
				tweetInfo[i]['clicks'] = (tweetInfo[i]['clicks'] or 0) + (float(c) / urlCounts[u]) # Divisor will always be >= 1.
	# Clean up unneeded raw click info.
	del tweetInfo[i]['raw_clicks']

# Traverse posts.
# There is no retweeting, so we don't need to worry about that. Still, other rules will be the same.
for i, pI in enumerate(postInfo):
	# There will be lots of nullifications, so treat that as our base case.
	postInfo[i]['clicks'] = None
	# Otherwise, traverse all links.
	for u, c in pI['raw_clicks'].iteritems():
		# Do nothing for URLs that have been retweeted, have no click info, or are shared across networks.
		# Otherwise, divide clicks by number of times link posted.
		if c and u not in retweetedUrls and len(urlNetworks[u]) == 1:
			postInfo[i]['clicks'] = (postInfo[i]['clicks'] or 0) + (float(c) / urlCounts[u]) # Divisor will always be >= 1.
	# Clean up unneeded raw click info.
	del postInfo[i]['raw_clicks']

# Whew, now the easy part: turn both arrays into dataframes.
tweetDf = pd.DataFrame(tweetInfo)
postDf = pd.DataFrame(postInfo)

# Write out.
tweetDf.to_csv(filePath_output % 'twitter', encoding='utf-8', index=False)
postDf.to_csv(filePath_output % 'facebook', encoding='utf-8', index=False)
