#!/usr/bin/env python

"""

This script will traverse consolidated Twitter/Facebook data and apply sentiment analysis techniques to all posts therein.

"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Organizations for which to perform sentiment analysis. Either a list or "all".
orgs = ['nytimes']



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
	# links.reverse()
	for link in links:
		message = message.replace(link,'')
	# Return.
	return message.strip()

"""
Map POS from pos_tag to Wordnet.
Reuses: https://github.com/linkTDP/BigDataAnalysis_TweetSentiment/blob/master/SentiWordnet.py
"""
def posTagToWn(posTag):
	if posTag.startswith('NN'):
		return wn.NOUN
	elif posTag.startswith('VB'):
		return wn.VERB
	elif posTag.startswith('JJ'):
		return wn.ADJ
	elif posTag.startswith('RB'):
		return wn.ADV
	else:
		return None

"""
Tokenize, tag, and sentiment-classify a message.
No need to clean text before passing here.
"""
def sentimentClassify(message):
	message = cleanMessage(message) # Clean.

	# Tokenize. Get meanings.
	sentences = nltk.sent_tokenize(message)
	sentenceTokens = [nltk.word_tokenize(s) for s in sentences]
	posTags = [nltk.pos_tag(st) for st in sentenceTokens]

	# Translate to Wordnet POS tags.
	wnPosTags = []
	for s in posTags:
		wnPosTags.append([(token,posTagToWn(pos)) for (token,pos) in s if posTagToWn(pos) is not None])

	# Get sense. Use lesk() to start; if failed, just take first sense.
	def wsd(tokens,token,pos):
		leskWsd = nltk.wsd.lesk(tokens,token,pos)
		if leskWsd:
			return leskWsd
		defaultWsd = wn.synsets(token,pos)
		if defaultWsd:
			return defaultWsd[0]
		return None;

	# This is a big design decision. Do we collapse the sentences into one long set of tokens for WSD?
	# It might be good to do so, as each set of text is about a focused topic and we can understand more by
	# considering it as a whole.
	# On the other hand, it might cause confusion among some words.
	# Decision: combine all text here. If we wanted to classify separately, the following code would have worked:
	# senses = []
	# for s in wnPosTags:
	# 	sentenceSenses = [(token, wsd(tokens,token,pos)) for (token,pos) in s]
	# 	sentenceSenses = [t for t in sentenceSenses if t[1] is not None]
	# 	senses.append(sentenceSenses)

	# Collapse list.
	wnPosTagsFlat = [item for sublist in wnPosTags for item in sublist]
	allTokens = [token for (token,_) in wnPosTagsFlat]

	# Calculate senses.
	senses = [(token, wsd(allTokens,token,pos)) for (token,pos) in wnPosTagsFlat]
	senses = [s for s in senses if s[1] is not None]

	# Aggregate score containers.
	aggScorePos = 0
	aggScoreNeg = 0

	# Score containers for "significant" (obj != 1) tokens.
	significantTokens = 0
	aggSigScorePos = 0
	aggSigScoreNeg = 0

	# Container for scoring information.
	scoreInfo = { 'tokens': [] }

	# Score.
	for (token, sense) in senses:
		# Score.
		swnEntry = swn.senti_synset(sense.name())
		if swnEntry is None:
			continue
		scoreInfo['tokens'].append((
			token, sense.name(),
			swnEntry.pos_score(),
			swnEntry.neg_score()
		))
		# Aggregates.
		aggScorePos += swnEntry.pos_score()
		aggScoreNeg += swnEntry.neg_score()
		# Significants.
		if swnEntry.pos_score() > 0 or swnEntry.neg_score() > 0:
			significantTokens += 1
			aggSigScorePos += swnEntry.pos_score()
			aggSigScoreNeg += swnEntry.neg_score()

	# Calculate means.
	# Aggregates.
	scoreInfo['aggScorePos'] = aggScorePos
	scoreInfo['aggScoreNeg'] = aggScoreNeg
	# Means.
	scoreInfo['meanScorePos'] = aggScorePos / max(1,len(scoreInfo['tokens']))
	scoreInfo['meanScoreNeg'] = aggScoreNeg / max(1,len(scoreInfo['tokens']))
	# Significants.
	scoreInfo['meanScorePosSig'] = aggSigScorePos / (significantTokens or 1)
	scoreInfo['meanScoreNegSig'] = aggSigScoreNeg / (significantTokens or 1)

	# Perform final classification.
	if (scoreInfo['aggScorePos'] > scoreInfo['aggScoreNeg']):
		scoreInfo['class'] = 'Positive'
	elif (scoreInfo['aggScorePos'] < scoreInfo['aggScoreNeg']):
		scoreInfo['class'] = 'Negative'
	else:
		scoreInfo['class'] = 'Neutral'

	return scoreInfo, len(allTokens)



##### Main Execution

# Iterate over all organizations.
for org, orgData in relevantOrgs.iteritems():
	# General settings.
	orgName = orgData['name']

	# Twitter. Start by getting configuration and printing status.
	sn = orgData['twitter']
	print 'Starting Twitter sentiment analysis for %s.' % orgName
	twitterStart = dt.datetime.now()

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

	# Iterate over tweets and extract sentiment information.
	for tweet in tweets:
		# Get text .
		text = tweet['text']
		# Classify.
		scoreInfo, tokenCount = sentimentClassify(text)
		# Stats.
		wordsTagged += len(scoreInfo['tokens'])
		tokensCounted += tokenCount
		if (len(scoreInfo['tokens'])):
			sentiments[tweet['id']] = scoreInfo
			postsTagged += 1
		else:
			sentiments[tweet['id']] = None
		# Append to dict.
		

	# Output.
	json.dump(sentiments,open(twitterSentimentDirectory+org+'.json','w'))

	# Status.
	print 'Done performing tweet sentiment analysis for %s.' % orgName
	print 'Posts:          %d' % postCount
	print 'Posts tagged:   %d' % postsTagged
	print 'Tokens counted: %d' % tokensCounted
	print 'Words tagged:   %d' % wordsTagged
	print 'Time: %.2f minutes.' % (((dt.datetime.now() - twitterStart).seconds)/60.0)
	print

	# Facebook. Start by getting configuration and printing status.
	user = orgData['facebook']
	print 'Starting Facebook sentiment analysis for %s.' % orgName
	facebookStart = dt.datetime.now()

	# Find posts.
	postsFilename = [f for f in os.listdir(consolidatedFbPostsDirectory) if f.find(org) == 0][-1]
	posts = json.load(open(consolidatedFbPostsDirectory+postsFilename))

	# Container for sentiments.
	sentiments = dict()

	# Stats.
	postCount = len(posts)
	postsTagged = 0
	tokensCounted = 0
	wordsTagged = 0

	# Iterate over posts and extract sentiment information.
	# Note that we'll score three things: the post, the headline, and the description, if all are present.
	# We will also put together an "aggregate" score using the combined text of all three.
	for post in posts:
		# Storage for all post sentiments.
		postSentiments = {}
		for field in ('message','name','description', 'agg'):
			# Get field.
			if (field == 'agg'):
				text = '. '.join([
					post['message'] if 'message' in post else '',
					post['name'] if 'name' in post else '',
					post['description'] if 'description' in post else ''
				])
			else:
				text = post[field] if field in post else ''
			# Classify.
			scoreInfo, tokenCount = sentimentClassify(text)
			# Stats.
			wordsTagged += len(scoreInfo['tokens'])
			tokensCounted += tokenCount
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
	print 'Time: %.2f minutes.' % (((dt.datetime.now() - facebookStart).seconds)/60.0)
	print

# Any cleanup goes here.
