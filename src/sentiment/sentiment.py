#!/usr/bin/env python

"""

This script will traverse consolidated Twitter/Facebook data and apply sentiment analysis techniques to all posts therein.

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Organizations for which to perform sentiment analysis. Either a list or "all".
orgs = 'all'



##### Main Setup

# Libraries.
import datetime as dt
import dateutil.parser
import json
import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus import sentiwordnet as swn
import os
import re
import socialUrlUtils

# Social data directories.
consolidatedTweetsDirectory  = '../../../data/twitter/consolidated/'
consolidatedFbPostsDirectory = '../../../data/facebook/consolidated/'
# Sentiment directories.
twitterSentimentDirectory  = '../../../data/sentiment/twitter/'
fbSentimentDirectory       = '../../../data/sentiment/facebook/'

# Organization setup.
allOrgs = json.load(open('../../conf/organizations.json'))
if type(orgs) == str:
	orgs = allOrgs.keys()
relevantOrgs = dict((k, allOrgs[k]) for k in orgs)



##### Functions

"""
Remove all URLs and usernames. Hashtags *should* be fine.
"""
def cleanMessage(message):
	# Remove @mentions.
	message = re.sub('@[a-zA-Z0-9]+','',message)
	# Remove links.
	links = socialUrlUtils.urlsInText(message)
	links.reverse()
	for link in links:
		message = message.replace(link,'')
	# Return.
	return message

"""
Tokenize, tag, and sentiment-classify a message.
No need to clean text before passing here.
"""
def sentimentClassify(message):
	message = cleanMessage(message) # Clean.

	# Tokenize. Get meanings.
	tokens = nltk.word_tokenize(message)
	meanings = [nltk.wsd.lesk(tokens,t) for t in tokens]

	# Aggregate score containers.
	aggScorePos = 0
	aggScoreNeg = 0
	aggScoreObj = 0

	# Container for scoring information.
	scoreInfo = { 'tokens': [] }

	# Score.
	for t, m in zip(tokens,meanings):
		# Only process words for which we have meanings.
		if m is None:
			continue
		# Score.
		swnEntry = swn.senti_synset(m.name())
		if swnEntry is None:
			continue
		scoreInfo['tokens'].append((
			t, m.name(),
			swnEntry.pos_score(),								# Positivity
			swnEntry.neg_score(),								# Negativity
			1 - (swnEntry.pos_score() + swnEntry.neg_score())	# Objectivity
		))
		# Aggregates.
		aggScorePos += swnEntry.pos_score()
		aggScoreNeg += swnEntry.neg_score()
		aggScoreObj += 1 - (swnEntry.pos_score() + swnEntry.neg_score())

	# Calculate means.
	scoreInfo['scorePos'] = aggScorePos / max(1,len(scoreInfo['tokens']))
	scoreInfo['scoreNeg'] = aggScoreNeg / max(1,len(scoreInfo['tokens']))
	scoreInfo['scoreObj'] = aggScoreObj / max(1,len(scoreInfo['tokens'])) if len(scoreInfo['tokens']) else 1

	# Perform final classification.
	if (scoreInfo['scorePos'] > scoreInfo['scoreNeg']):
		scoreInfo['class'] = 'Positive'
	elif (scoreInfo['scorePos'] < scoreInfo['scoreNeg']):
		scoreInfo['class'] = 'Negative'
	else:
		scoreInfo['class'] = 'Neutral'

	return scoreInfo, len(tokens)



##### Main Execution

# Iterate over all organizations.
for org, orgData in relevantOrgs.iteritems():
	# General settings.
	orgName = orgData['name']

	# Twitter. Start by getting configuration and printing status.
	sn = orgData['twitter']
	print 'Starting Twitter sentiment analysis for %s.' % orgName

	# Find tweets.
	tweetsFilename = [f for f in os.listdir(consolidatedTweetsDirectory) if f.find(org) == 0][-1]
	tweets = json.load(open(consolidatedTweetsDirectory+tweetsFilename))

	# Container for sentiments.
	sentiments = dict()

	# Stats.
	postCount = len(tweets)
	postsTagged = 0
	tokensCounted = 0
	wordsTagged = 0

	# Iterate over them and extract sentiment information.
	for tweet in tweets:
		# Get text .
		text = tweet['text']
		# Classify.
		scoreInfo, tokenCount = sentimentClassify(text)
		# Stats.
		wordsTagged += len(scoreInfo['tokens'])
		if (len(scoreInfo['tokens'])):
			scoreInfo['scored'] = True
			postsTagged += 1
		else:
			scoreInfo['scored'] = False
		# Append to dict.
		sentiments[tweet['id']] = scoreInfo

	# Output.
	json.dump(sentiments,open(twitterSentimentDirectory+org+'.json','w'))

	# Status.
	print 'Done performing tweet sentiment analysis for %s.' % orgName
	print 'Posts:          %d' % postCount
	print 'Posts tagged:   %d' % postsTagged
	print 'Tokens counted: %d' % tokensCounted
	print 'Words tagged:   %d' % wordsTagged
	print

	# Facebook. Start by getting configuration and printing status.
	user = orgData['facebook']
	print 'Starting Facebook sentiment analysis for %s.' % orgName

	# Container for sentiments.
	sentiments = dict()

	# Stats.
	postCount = len(tweets)
	postsTagged = 0
	tokensCounted = 0
	wordsTagged = 0

	# Find posts.
	postsFilename = [f for f in os.listdir(consolidatedFbPostsDirectory) if f.find(org) == 0][-1]
	posts = json.load(open(consolidatedFbPostsDirectory+postsFilename))

	# Iterate over them and extract sentiment information.
	# Note that we'll score three things: the post, the headline, and the description, if all are present.
	for post in posts:
		# Storage for all post sentiments.
		postSentiments = {}
		for field in ('message','name','description'):
			# Get field.
			text = post[field] if field in post else ''
			# Classify.
			scoreInfo, tokenCount = sentimentClassify(text)
			# Stats.
			wordsTagged += len(scoreInfo['tokens'])
			scoreInfo['scored'] = bool(len(scoreInfo['tokens']))
			# Append to post sentiments.
			postSentiments[field] = scoreInfo
		# Stats.
		postsTagged += 1 if sum([len(info['tokens']) for info in postSentiments.values()]) else 0
		# Append to dict.
		sentiments[post['id']] = postSentiments

	# Output.
	json.dump(sentiments,open(fbSentimentDirectory+org+'.json','w'))

	# Status.
	print 'Done performing Facebook post sentiment analysis for %s.' % orgName
	print 'Posts:          %d' % postCount
	print 'Posts tagged:   %d' % postsTagged
	print 'Tokens counted: %d' % tokensCounted
	print 'Words tagged:   %d' % wordsTagged
	print

# Any cleanup goes here.
