from flask import Flask, send_file, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
import math
from math import radians, cos, sin, asin, sqrt
import re
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

from bokeh.io import output_file, show
from bokeh.embed import components, file_html
from bokeh.models import CategoricalColorMapper, HoverTool, Legend, Range1d
from bokeh.core.properties import value
from bokeh.palettes import Category20c
from bokeh.plotting import figure, output_file, show
from bokeh.transform import cumsum
from bokeh.resources import CDN

'''
The statement_extract function takes in a bank statement in the form of a csv
of the format ('Posted Date', 'Reference Number', 'Payee', 'Address', 'Amount').
From this csv, it extracts San Francisco businesses and the amounts spent at
them. This prototype was built to read only Bank of America statments and
my own personal 4 month transaction history was used as a demonstration.
'''
def statement_extract(csv):

    transactions = pd.read_csv(csv)
    transactions.dropna()
    transactions = transactions.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    transactions = transactions[transactions['Address'].str.lower() == 'san francisco ca']

    transactions['Payee'] = transactions['Payee'].str.lower()
    transactions['Payee'] = transactions['Payee'].str.replace('san franciscoca', '')

    businesses = []

    for business in transactions['Payee']:
        if '*' in business:
            business = business.split('*')[1]
        if '-' in business:
            business = business.split('-')[0]
        if '#' in business:
            business = business.split('#')[0]
        if '.' in business:
            business = business.split('.')[0]
        if '(' in business:
            business = business.split('(')[0]

        regex = re.compile(r'[0-9]{2,}')
        if regex.search(business):
            business = re.sub(regex, '', business)

        city_stopwords = ['potrero', 'fillmore', 'deli', 'whse', 'llc', 'tru', 'lndry', 'union sq', 'sfo', 'usa',
                          'marina']

        for stopword in city_stopwords:
            if stopword in business:
                business = business.replace(stopword, '')

        businesses.append(business.strip())

        spendings = {}

        for place in businesses:
            matches = transactions[transactions['Payee'].str.contains(place, case=False)]
            matches = matches.reset_index()
            purchases = []
            for idx in range(0, len(matches)):
                month = matches['Posted Date'][idx][:2]
                amt = (matches['Amount'][idx])*(-1)
                purchases.append((month, amt))
            spendings[place] = purchases

    return businesses, spendings

'''
Inputs:
 - business: business name to get recs for
 - df: pandas dataframe of SF businesses
 - matrix: array with all numeric values from df
Outputs:
 - final_recs: list of top 5 overall business recs
 - save_money_recs: dictionary of only cheaper business recs
 - higher_rated_recs: dictionary of both cheaper and higher rated business recs
Function:
 - calculates the cosine similarity between all businesses in df
 - finds businesses most similar to the business input
 - weights these similar businesses by distance and number of matching categories
'''
def best_business_recs(business, matrix, df):

    # calulate cosine similarity between all rows in matrix
    cosine_sim = cosine_similarity(matrix, matrix)

    # locate business of interest and sort all cosine_sim's with that row
    idx = df.loc[df.business == business].index[0]
    scores = cosine_sim[idx,:]
    ordered = scores.argsort()[::-1]

    matches = []
    match_locations = []
    categories = []
    bus_lat = df['lat'][idx]
    bus_lng = df['lng'][idx]

    for col in df.columns:
        if df[col][idx] == 1:
            categories.append(col)

    # count all matching business categories and absolute lat/lng distance
    for similar_business in ordered[1:26]:
        count = 0
        for category in categories:
            if df[category][similar_business] == 1:
                count += 1

        match_lat = df['lat'][similar_business]
        match_lng = df['lng'][similar_business]

        distance = abs(haversine(bus_lng, bus_lat, match_lng, match_lat))

        match_locations.append((similar_business, distance))
        matches.append((similar_business, count))

    sorted_category_matches = sorted(matches, key=lambda x: x[1], reverse=True)
    sorted_location_matches = sorted(match_locations, key=lambda x: x[1])

    weighted_matches = []

    # weight each rec on their order of appearance in cosine_sim, categories, and distance
    for item in ordered[1:26]:
        weight_cos = np.where(ordered==item)[0]
        weight_cat = [index for index, tup in enumerate(sorted_category_matches) if tup[0] == item][0]
        weight_loc = [index for index, tup in enumerate(sorted_location_matches) if tup[0] == item][0]

        weight = weight_cos + weight_cat + weight_loc

        weighted_matches.append((item, weight))

    weighted_matches = sorted(weighted_matches, key=lambda x: x[1])

    business_recs = []

    for tup in weighted_matches[:15]:
        business_recs.append(tup[0])

    # find cheaper and better rated businesses
    save_money_recs = {}
    higher_rated_recs = {}

    cheaper_places = []
    higher_rated_places = []

    for rec in business_recs:
        if df['price'][rec] < df['price'][idx]:
            name = df['business'][rec]
            price = df['price'][rec]
            rating = df['rating'][rec]
            pic = df['image_url'][rec]
            link = df['url'][rec]
            category = df['business_type'][rec]
            rec_dict = {"name": name, "price": price, "pic": pic, "link":link, "rating": rating, "category": category}
            cheaper_places.append(rec_dict)
            if df['rating'][rec] > df['rating'][idx]:
                name = df['business'][rec]
                price = df['price'][rec]
                rating = df['rating'][rec]
                pic = df['image_url'][rec]
                link = df['url'][rec]
                category = df['business_type'][rec]
                higher_rated_dict = {"name": name, "price": price, "pic": pic, "link":link, "rating": rating, "category": category}
                higher_rated_places.append(higher_rated_dict)

    save_money_recs[df['business'][idx]] = cheaper_places
    higher_rated_recs[df['business'][idx]] = higher_rated_places

    final_recs = []

    # get business names for return and remove repeats
    for bus in business_recs:
        rec = df['business'][bus]
        if rec not in final_recs:
            if rec != df['business'][idx]:
                final_recs.append(rec)

    return final_recs[:5], save_money_recs, higher_rated_recs

'''
Inputs:
 - extracted_business_list: list of business names
 - spendings: dictionary of business visited including when and how much was spent.
 - df: pandas dataframe of SF businesses
 - num_matrix: array with all numeric values from df
Outputs:
 - all_monthly_recs: list of all recs
 - save_money_recs: dictionary of only cheaper business recs
 - higher_rated_recs: dictionary of both cheaper and higher rated business recs
 - category_counts: dictionary of business categories match counts
 - spendings_dict: dictionary of businesses visited including when and how much was spent.
Function:
 - gets recommendations for each business in the extracted_business_list
'''
def statement_to_recs(extracted_business_list, spendings, num_matrix, df):

    all_monthly_recs = []
    save_money_recs = {}
    higher_rated_recs = {}
    category_counts = defaultdict(int)
    spendings_dict = {}

    for place in clean_statement_list:

        try:
            matches = df[df['business'].str.contains(place, case=False)]

            matches = matches.reset_index()
            business_match = matches['business'][0]

            for col in matches.columns:
                if matches[col][0] == 1:
                    category_counts[col] +=1

            spent = spendings[place]
            spendings_dict[business_match] = spent

            all_recs, cheap_recs, best_recs = best_business_recs(business_match, num_matrix, df)

            for rec in all_recs:
                all_monthly_recs.append(rec)
            for key, value in cheap_recs.items():
                save_money_recs[key] = value
            for key, value in best_recs.items():
                higher_rated_recs[key] = value

        except:
            pass

    return all_monthly_recs, save_money_recs, higher_rated_recs, category_counts, spendings_dict

'''
Inputs:
  - spendings_dict: dictionary of business visited including when and how much was spent.
  - df: pandas dataframe of SF businesses
 Outputs:
  - script, div: bokeh components for plotting
  - food, services, bars, retail, coffee: lists with sums of amounts spent in each category
 Function:
  - creates a multiline bokeh plot of spendings by month broken into 5 categories
'''
def spendings_plot(spendings_dict, df):

    food12 = []
    coffee12 = []
    services12 = []
    retail12 = []
    bars12 = []

    food01 = []
    coffee01 = []
    services01 = []
    retail01 = []
    bars01 = []

    food02 = []
    coffee02 = []
    services02 = []
    retail02 = []
    bars02 = []

    food03 = []
    coffee03 = []
    services03 = []
    retail03 = []
    bars03 = []

    food = []
    coffee = []
    services = []
    retail = []
    bars = []

    months = ['12', '01', '02', '03']

    data = { 'Month': months }

    for key, value in spendings_dict.items():
        matches = df[df['business'].str.contains(key, case=False)]
        matches = matches.reset_index()
        category = matches['business_type'][0]

        if category == 'food':
            for amt in value:
                if amt[0] == '12':
                    food12.append(amt[1])
                elif amt[0] == '01':
                    food01.append(amt[1])
                elif amt[0] == '02':
                    food02.append(amt[1])
                elif amt[0] == '03':
                    food03.append(amt[1])
        elif category == 'coffee':
            for amt in value:
                if amt[0] == '12':
                    coffee12.append(amt[1])
                elif amt[0] == '01':
                    coffee01.append(amt[1])
                elif amt[0] == '02':
                    coffee02.append(amt[1])
                elif amt[0] == '03':
                    coffee03.append(amt[1])
        elif category == 'services':
            for amt in value:
                if amt[0] == '12':
                    services12.append(amt[1])
                elif amt[0] == '01':
                    services01.append(amt[1])
                elif amt[0] == '02':
                    services02.append(amt[1])
                elif amt[0] == '03':
                    services03.append(amt[1])
        elif category == 'bars':
            for amt in value:
                if amt[0] == '12':
                    bars12.append(amt[1])
                elif amt[0] == '01':
                    bars01.append(amt[1])
                elif amt[0] == '02':
                    bars02.append(amt[1])
                elif amt[0] == '03':
                    bars03.append(amt[1])
        elif category == 'retail':
            for amt in value:
                if amt[0] == '12':
                    retail12.append(amt[1])
                elif amt[0] == '01':
                    retail01.append(amt[1])
                elif amt[0] == '02':
                    retail02.append(amt[1])
                elif amt[0] == '03':
                    retail03.append(amt[1])

    food.append(sum(food12))
    food.append(sum(food01))
    food.append(sum(food02))
    food.append(sum(food03))

    bars.append(sum(bars12))
    bars.append(sum(bars01))
    bars.append(sum(bars02))
    bars.append(sum(bars03))

    coffee.append(sum(coffee12))
    coffee.append(sum(coffee01))
    coffee.append(sum(coffee02))
    coffee.append(sum(coffee03))

    retail.append(sum(retail12))
    retail.append(sum(retail01))
    retail.append(sum(retail02))
    retail.append(sum(retail03))

    services.append(sum(services12))
    services.append(sum(services01))
    services.append(sum(services02))
    services.append(sum(services03))

    colors = ['#78aac3', '#f07bbb', '#658138', '#dab48d', '#c8d5f6']
    legends_list = ['Food', 'Coffee', 'Retail', 'Services', 'Bars']
    ys=[food, coffee, retail, services, bars]
    xs=[months, months, months, months, months]

    p = figure(x_range=months, plot_width=700, plot_height=500,title="Monthly Spending Per Category", x_axis_label="Month", y_axis_label="Amount Spent")

    for (colr, leg, x, y ) in zip(colors, legends_list, xs, ys):
        p.line(x, y, color= colr, line_width=4, legend= leg)

    p.legend.location = "center_right"


    script, div = components(p)

    return script, div, food, services, bars, coffee, retail

'''
Inputs:
 - lng1, lat1: latitude and longitude of business visited
 - lng1, lat2: latitude and longitude of business recommended
Function:
 - caluclated the haversine distance between 2 businesses
'''
def haversine(lng1, lat1, lng2, lat2):

    # convert decimal degrees to radians
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])

    # haversine formula
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    r = 3956 # Radius of earth in miles
    return c * r
