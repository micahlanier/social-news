Prediction: Brainstorming
=========================

This is a collection of thoughts about the regression problems that we might be able to tackle with our data. It addresses the sorts of questions that we might want to answer, the variables we have available, and the models that we may employ.

Outcomes
--------
Outcomes worthy of measure are fairly straightforward: link clicks and social media engagement.
- Link clicks: measured with Bitly and somewhat unevenly available across organizations
- Facebook likes/shares/comments
- Twitter retweets/favorites (favorites are low-value because they have low public importance)

Features
--------
Here are some potential feature categories that we can use:
- Tweet/post engagement features (potentially interesting for the clicks outcome):
    + Twitter retweets/favorites
    + Facebook likes/shares/comments
- Tweet/post content features:
    + Categorical Facebook media variable
    + Categorical Twitter media variable
- News organization features:
    + Organization itself (25-level factor)
    + Organization category
- Text features:
    + Topics?
    + Sentiment
    + Word counts
    + Hashtags (count, binary "usage" feature, etc.)
    + Link position (for Facebook)
    + Rudimentary categorization
- Time features:
    + Time of day (possibly a polynomial or oscillation function)
    + Day of week
    + Date (invalid for future-prediction tasks)

All outcomes should probably be adjusted by follower/liker counts. But we may wish to consider using those values as features *after* adjustment. This may give an indication of the "network value" of a larger audience.

Models
------
Very little of our coursework addressed regularization, so we probably won't get much help from past material. Here are three models that I think we ought to consider:
- Linear regression (ideally with regularization): http://scikit-learn.org/stable/modules/linear_model.html
- Random Forest regression: http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
- SVM regression (Support Vector Regression): http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
All models can use tuning to maximize accuracy and minimize overfitting.

For evaluation, these appear to be standard criteria:
1. RMSE (root mean square error): measure of the average difference between the prediction and real outcome.
2. Interpretability: linear regression seems to win by default on this measure.

We may want to choose both the most accurate model and the most interpretable model for reporting.
