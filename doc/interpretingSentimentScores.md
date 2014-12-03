Interpreting Sentiment Scores
=============================

Sentiment scores are keyed based on social network post ID (tweet ID/Facebook post ID). Numeric scores follow SentiWordNet standards: all identified words have positivity, negativity, and objectivity scores that *must* sum to 1. Only the first two categories are recorded, as they are most interesting (and the third can be derived from the other two).

Key Fields
----------
This section describes key fields for analysis. The sections below give further information for those interested.

There are three fields of partical utility:
- `class`: Gives a three-way classification (postive/negative/netural) for each post.
- `meanScoreNegSig`/`meanScorePosSig`: The sums of all negative and positive scores divided by the number of "significant" terms in the message (those with positive or negative scores greater than 1). **These scores are comparable across social networks.**

Additionally, Facebook sentiments feature four keys. Our analysis focuses on sentiment fields from two: **message** (the post text, comparable to a tweet) and **agg** (the entire post sentiment, *not* comparable to a tweet).

---

Fields
------
Each sentiment classification contains several scores/labels. Here is the meaning behind each and how you should use them.

- `class`: Gives a three-way classification (postive/negative/netural) for each post.
- `tokens`: An enumeration of the words that were identified and used for scoring. You will probably find little utility here aside from the chance to see how certain words were scored or taking the length of this entity to determine how many terms were used in scoring. Each entry contains the word, its WordNet definition, positivity score, and negativity score.
- `aggScoreNeg`/`aggScorePos`: The sums of all negative and positive scores for the message. **These scores are useful to convey sentiment within social networks**, because in-network posts are are comparable length.
- `meanScoreNegSig`/`meanScorePosSig`: The sums of all negative and positive scores divided by the number of "significant" terms in the message (those with positive or negative scores greater than 1). **These scores are useful to convey sentiment within and between social networks.**
- `meanScoreNeg`/`meanScorePos`: The sums of all negative and positive scores divided by the number of sentimental tokens (including those with no positive/negative sentiment). These numbers tend to be closest to zero and perhaps better reflect overall sentiment, as both positive and negative scores are reduced if there are more objective terms.

Facebook
--------
Note that Facebook sentiments have four keys. See the following for explanations of each:

- `agg`: An aggregation of all below categories. Note that this is more than a sum of all three. The word sense disambiguation process (the method for determining the actual meaning of each word) takes advantage of aggregation and aims to produce more accurate classifications than any of the three categories alone.
- `description`: The description of an accompanying link. Typically two or three sentences.
- `message`: The body of the post itself.
- `name`: The title of a link that accompanies the post.

If you are simply interested in one set of scores, the `agg` scores will probably be most useful.