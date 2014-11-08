#!/usr/bin/env python

"""

TODO


"""

##### Configuration

# Edit things here to your liking. But please don't commit them needlessly.

# Specify sources. Either one or both.
sources = ['twitter','facebook']



##### Main Setup

# Libraries.
import json
import os
import pandas as pd
from urlparse import urlparse

# Data directories.
pathConsolidated = '../../../data/%s/consolidated/'

# Get all files to traverse. Assume that we can get everything in consolidated folder.
postFiles = []
for source in sources:
	sourcePath = pathConsolidated % source
	postFiles += [(source,p[:p.find('-')],sourcePath + p) for p in os.listdir(sourcePath) if p[-5:] == '.json']



##### Helper Functions

"""
Return a list of expanded URLs regardless of service.
"""
def associatedUrls(network,post):
	if network == 'facebook' and 'link' in post:
		return [post['link']]
	elif network == 'twitter':
		return [u['expanded_url'] for u in post['entities']['urls']]
	return []



##### Get URLs

# Though we're only interested in counts right now, we might want to analyze more later.
# Just in case, store data in a data frame.
rawUrlData = pd.DataFrame()

# Track count of posts with no associated URLs.
postsSansUrl = 0

# Traverse files.
for (network, sn, pf) in postFiles:
	# Status.
	print 'Beginning analysis of %s user @%s' % (network.title(), sn)
	# Get all posts and traverse.
	posts = json.load(open(pf))
	for post in posts:
		# Get links and traverse.
		urls = associatedUrls(network,post)
		if len(urls) == 0:
			postsSansUrl += 1
		for url in urls:
			# Now we have the URL. Get any features that we're interested in.
			urlDomain = urlparse(url).netloc
			# Add to our data frame.
			rawUrlData = rawUrlData.append(pd.DataFrame(dict({
				'network': [network],
				'sn': [sn],
				'domain': [urlDomain]
			})))

# Cleanup.
rawUrlData.reset_index(drop=True, inplace=True)



##### Aggregate and Output

# Statistics by account/network.
statsByNetworkAccount = rawUrlData.copy()
statsByNetworkAccount['posts'] = 1
statsByNetworkAccount = statsByNetworkAccount.groupby(['network','sn','domain']).count().reset_index()
statsByNetworkAccount.sort(['network','sn','posts','domain'], ascending=[True,True,False,True], inplace=True)
statsByNetworkAccount.to_csv('../../../data/urls/stats/domainsByNetworkAccount.tsv', sep='\t', index=False)

# Statistics by domain.
statsByDomain = rawUrlData[['domain']]
statsByDomain['posts'] = 1
statsByDomain = statsByDomain.groupby(['domain']).count().reset_index()
statsByDomain.sort(['posts'], ascending=[False], inplace=True)
statsByDomain.to_csv('../../../data/urls/stats/domains.tsv', sep='\t', index=False)

# Status.
print 'Posts without a URL: %d' % postsSansUrl
