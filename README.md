social-news
===========

Project for AC 209 social news analysis.

Configuration
-------------

### Local Setup

TODO: More.

### Twitter Access
To access the Twitter API, you need to use your Twitter account to register an [app](https://apps.twitter.com). It's easy to do: just create one named something like "My Twitter Analysis"—nobody needs to approve it or anything.

Once you have created your app, visit the "Keys and Access Tokens" tab.

TODO: Python instructions.

TODO: More.

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
  * facebook/: Code for pulling from Facebook.
  * twitter/: Code for pulling from Twitter.
