from flask import Flask, send_file, render_template, request, jsonify, flash, redirect, url_for, send_from_directory
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from recommender_api import clean_statement, best_business_recs, statement_to_recs, spendings_plot, haversine
from math import radians, cos, sin, asin, sqrt

from bokeh.io import output_file, show
from bokeh.embed import components, file_html
from bokeh.models import CategoricalColorMapper, HoverTool, Legend, Range1d
from bokeh.core.properties import value
from bokeh.palettes import Category20c
from bokeh.plotting import figure, output_file, show
from bokeh.transform import cumsum
from bokeh.resources import CDN

import pickle
import numpy as np
import pandas as pd
import os
import re
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

UPLOAD_FOLDER = '/Users/kari/ds/metis/metisgh/kojak/flask_app'
ALLOWED_EXTENSIONS = set(['csv'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Bootstrap(app)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Incorrect File Extension')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No File Entered')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file', filename=filename))
    return render_template("homepage.html")


@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    return redirect(url_for('user_recs', filename=filename))

return jsonify(spending_dicts)

@app.route('/recs/<filename>', methods=["POST", "GET"])
def user_recs(filename):

    num_matrix = pd.read_pickle("./num_matrix.pkl")
    df = pd.read_pickle('./final_df.pkl')

    statement = '/Users/kari/ds/metis/metisgh/kojak/flask_app/' + filename
    extracted_business_list, spendings = statement_extract(statement)
    all_recs, cheap_recs, high_rates_recs, category_counts, spendings_dict = statement_to_recs(extracted_business_list, spendings, num_matrix, df)

    no_matches = []
    for key, value in cheap_recs.items():
        if len(value) < 1:
            no_matches.append(key)

    for key in no_matches:
        del cheap_recs[key]

    no_matches_rate = []
    for key, value in high_rates_recs.items():
        if len(value) < 1:
            no_matches_rate.append(key)

    for key in no_matches_rate:
        del high_rates_recs[key]

    rec_breakdown = {}
    category_total = 0
    for key, value in category_counts.items():
        category_total = category_total + value
    for key, value in category_counts.items():
        rec_breakdown[key] = value/category_total

    food = {}
    coffee = {}
    bars = {}
    services = {}
    retail = {}

    for key, value in spendings_dict.items():
        matches = df[df['business'].str.contains(key, case=False)]
        matches = matches.reset_index()
        category = matches['business_type'][0]

        if category == 'food':
            total_spent = 0
            for amt in value:
                total_spent = total_spent + amt[1]
            food[key] = total_spent
        elif category == 'coffee':
            total_spent = 0
            for amt in value:
                total_spent = total_spent + amt[1]
            coffee[key] = total_spent
        elif category == 'retail':
            total_spent = 0
            for amt in value:
                total_spent = total_spent + amt[1]
            retail[key] = total_spent
        elif category == 'services':
            total_spent = 0
            for amt in value:
                total_spent = total_spent + amt[1]
            services[key] = total_spent
        elif category == 'bars':
            total_spent = 0
            for amt in value:
                total_spent = total_spent + amt[1]
            bars[key] = total_spent

    coffee_visited_tiers = []
    food_visited_tiers = []
    services_used_tiers = []
    bars_visited_tiers = []
    retail_visited_tiers = []

    for key, value in coffee.items():
        matches = df[df['business'].str.contains(key, case=False)]
        matches = matches.reset_index()
        price = matches['price'][0]
        coffee_visited_tiers.append(price)

    for key, value in food.items():
        matches = df[df['business'].str.contains(key, case=False)]
        matches = matches.reset_index()
        price = matches['price'][0]
        food_visited_tiers.append(price)

    for key, value in bars.items():
        matches = df[df['business'].str.contains(key, case=False)]
        matches = matches.reset_index()
        price = matches['price'][0]
        bars_visited_tiers.append(price)

    for key, value in services.items():
        matches = df[df['business'].str.contains(key, case=False)]
        matches = matches.reset_index()
        price = matches['price'][0]
        services_used_tiers.append(price)

    for key, value in retail.items():
        matches = df[df['business'].str.contains(key, case=False)]
        matches = matches.reset_index()
        price = matches['price'][0]
        retail_visited_tiers.append(price)

    coffee_recs_tiers = []
    food_recs_tiers = []
    services_recs_tiers = []
    bars_recs_tiers = []
    retail_recs_tiers = []

    for key, value in high_rates_recs.items():
        for rec in value:
            type = rec['category']
            if type == "coffee":
                coffee_recs_tiers.append(rec['price'])
            elif type == "food":
                food_recs_tiers.append(rec['price'])
            elif type == "retail":
                retail_recs_tiers.append(rec['price'])
            elif type == "services":
                services_recs_tiers.append(rec['price'])
            elif type == "bars":
                bars_recs_tiers.append(rec['price'])

    coffee_spent_avg = sum(coffee_visited_tiers)/len(coffee_visited_tiers)
    food_spent_avg = sum(food_visited_tiers)/len(food_visited_tiers)
    bars_spent_avg = sum(bars_visited_tiers)/len(bars_visited_tiers)
    retail_spent_avg = sum(retail_visited_tiers)/len(retail_visited_tiers)
    try:
        services_spent_avg = sum(services_used_tiers)/len(services_used_tiers)
    except:
        pass

    coffee_rec_avg = sum(coffee_recs_tiers)/len(coffee_recs_tiers)
    food_rec_avg = sum(food_recs_tiers)/len(food_recs_tiers)
    bars_rec_avg = sum(bars_recs_tiers)/len(bars_recs_tiers)
    retail_rec_avg = sum(retail_recs_tiers)/len(retail_recs_tiers)
    try:
        services_rec_avg = sum(services_recs_tiers)/len(services_recs_tiers)
    except:
        pass

    total_food = sum(food.values())
    total_coffee = sum(coffee.values())
    total_bars = sum(bars.values())
    total_services = sum(services.values())
    total_retail = sum(retail.values())

    coffee_savings_avg = (((coffee_spent_avg - coffee_rec_avg) * (0.4)) * total_coffee)/4
    food_savings_avg = (((food_spent_avg - food_rec_avg) * (0.4)) * total_food)/4
    bars_savings_avg = (((bars_spent_avg - bars_rec_avg) * (0.4)) * total_bars)/4
    retail_savings_avg = (((retail_spent_avg - retail_rec_avg) * (0.4)) * total_retail)/4
    try:
        services_savings_avg = (((services_spent_avg - services_rec_avg) * (0.4)) * total_services)/4
    except:
        pass

    script, div, food_monthly, services_monthly, bars_monthly, coffee_monthly, retail_monthly = spendings_plot(spendings_dict, df)

    recs_list = []

    for key, value in high_rates_recs.items():
        for rec in value:
            if rec not in recs_list:
                recs_list.append(rec)

    return render_template("recspage.html", cheapdict=cheap_recs, best_rating=recs_list,rec_breakdown=rec_breakdown,
                            spendings=spendings_dict, food=food, coffee=coffee,bars=bars, services=services, retail=retail,
                            script=script, div=div, food_monthly=food_monthly, services_monthly=services_monthly,
                            bars_monthly=bars_monthly, coffee_monthly=coffee_monthly, retail_monthly=retail_monthly,
                            averagecoffee=coffee_savings_avg, averagefood=food_savings_avg, averagebars=bars_savings_avg,
                            averageretail=retail_savings_avg)

@app.route('/recs/business', methods=["POST", "GET"])
def business_recs():

    num_matrix = pd.read_pickle("./num_matrix.pkl")
    df = pd.read_pickle('./final_df.pkl')

    business = request.args.get('name')
    matches = df[df['business'].str.contains(business, case=False)]

    matches = matches.reset_index()
    business_match = matches['business'][0]

    business_categories = []

    for col in matches.columns:
        if matches[col][0] == 1:
            business_categories.append(col)

    categories =  ",".join(business_categories)

    all_recs, cheap_recs, best_recs = best_business_recs(business_match, num_matrix, df)


    return render_template("businessrecspage.html", business_match=business_match, cheapdict=cheap_recs,
                            best_rating_dict=best_recs, price=matches['price'][0], categories=categories,
                            reviews=matches['review_count'][0], rating=matches['rating'][0], link=matches['url'][0],
                            pic=matches['image_url'][0])


    if __name__ == '__main__':
        app.run()
