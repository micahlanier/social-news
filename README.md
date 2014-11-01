social-news
===========

Project for AC 209 social news analysis.

Configuration
-------------

### Local Setup

To get started, create a folder to hold all of your work (I call mine "Final"). Create a couple of folders therein: **conf** (for machine-specific configuration) and **data** (for data). Then checkout the repo from GitHub. You can use GitHub's software or execute the following from the command line:

	git clone https://github.com/micahlanier/social-news

Once you have downloaded the repo, copy the contents of `[repo-root]/conf/local-templates/` to the **conf** folder you created above. You'll use the files in there to set up access credentials to third party APIs as needed.

### Twitter Access
To access the Twitter API, you need to use your Twitter account to register an [app](https://apps.twitter.com). It's easy to do: just create one named something like "My Twitter Analysis"—nobody needs to approve it or anything.

Once you have created your app, visit the "Keys and Access Tokens" tab. There, you'll find your client credentials that you can use to request an OAuth 2 (*not* 1) access key. There are several ways to make that request, but I (Micah) have only done so using Twython. Install Twython as you would install any Python library (`[sudo] pip install twython` on UNIX-like systems). Follow [Twython's instructions](https://twython.readthedocs.org/en/latest/usage/starting_out.html#oauth-2-application-authentication) and copy the access token in the `accessToken` field in your local conf/twitter.json file.

There are places to store your API key and secret in that file. Feel free to do so but no scripts currently use anything but the access token.

### Facebook Access
Accessing the Facebook Graph API is pretty easy. Simply visit Facebook's [Developer Tools](https://developers.facebook.com/tools/) page and click on the Graph API Explorer. Then click "Get Access Token" on top and one will be generated for you and inserted into the field at the top of the page.

Copy that value into the `accessToken` field in your local conf/facebook.json file. Note that this token only lasts for an hour or so. You will need to repeat this process if your token expires.

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
