# Project 3: MLB Pitcher Injury Prediction with Linear SVM Classification

This project explores MLB game and player statistics as well as pitching repertoire to make predictions for pitcher injuries in the following season. The features were then put into several classification models to determine the model with the most predictive power which was a Linear SVM.

This repo includes 7 files:

- **Data_Gathering.ipynb:** My code for gathering data from Sportrac.com for the Disabled List data and BrooksBaseball.com for Player Card data.
- **Data_Exploration.ipynb:** Code for exploring feature correlations with injuries.
- **Pitcher_Data_Cleaning.ipynb:** Includes code for Cleaning my dataset and splitting data into train and test sets by season.
- **Modeling.ipynb:** Includes code for oversampling and all classification models trained on previous seasons with hold-out data from the 2018 season injuries.
- **Project_Slides.pptx:** Final project slides overviewing analysis and results.
- **pitch_predict_app.py:** Code for my Flask app including home page as well as player pages.
- **pitch_predict_api.py:** Code for all of the functions called in my Flask app.
