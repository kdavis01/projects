# Spend + Save: Tailored Savings Recommendations Based on Your Spending Habits

This project uses the Yelp Fusion API and Google Places API business data in San Francisco to create content based recommendations based on your credit card transaction history.

This repo includes 5 files:

- yelp_review_topic_modeling.ipynb: Code includes topic modeling on yelp business reviews using TF-IDF vectorization and NMF to get 15 topics. Each business is given a topic vector for similarity comparison.
- data_cleaning.ipynb: Code includes combining of Yelp and Google API data, general data cleaning, and KNN imputation of missing business pricing values.
- recommender_app.py: Code for flask app recommender. The app takes in a csv upload of credit card transactions and returns spending breakdown, recommendations, and estimated savings impact of recommendations.
- recommender_api.py: Includes all functions used for recommendations, spending graphs, and bank statement cleaning.
- project_slides.pptx: Final project slides overviewing process and results.
