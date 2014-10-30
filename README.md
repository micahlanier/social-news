social-news
===========

Project for AC 209 social news analysis.

Configuration
-------------

### Local Setup

To get started, create a folder to hold all of your work (I call mine "Final"). Create a couple of folders therein: **conf** (for machine-specific configuration) and **data** (for data). Then checkout the repo from GitHub. You can use GitHub's software or execute the following from the command line:

	git clone https://github.com/micahlanier/social-news

### Twitter Access
To access the Twitter API, you need to use your Twitter account to register an [app](https://apps.twitter.com). It's easy to do: just create one named something like "My Twitter Analysis"—nobody needs to approve it or anything.

Once you have created your app, visit the "Keys and Access Tokens" tab. There, you'll find your client credentials that you can use to request an access key. There are ways to make that request, but I (Micah) have only done so using Twython

Install Twython as you would install any Python library (`[sudo] pip install twython` on UNIX-like systems). TODO: More.

### Facebook Access
Accessing the Facebook Graph API is pretty easy. Simply visit Facebook's [Developer Tools](https://developers.facebook.com/tools/) page and click on the Graph API Explorer. Then click "Get Access Token" on top and one will be generated for you and inserted into the field at the top of the page.

TODO: More.

Files
-----
The root directory of this repository contains the following directories. Please keep up-to-date :-).

* /conf/: Configuration files. Do not store keys or access credentials, please!
	* local-templates: Templates for local configuration files.
* /data/: Data. Please store voluminous data on Dropbox—only limited, static data should go here.
* /doc/: Documentation.
* /log/: Any notes that don't fit easily in git commits.
* /ref/: Reference materials.
* /src/: Source files.
	* ipynb/: iPython notebooks.
	* fb/: Code for pulling from Facebook.
	* twitter/: Code for pulling from Twitter.
