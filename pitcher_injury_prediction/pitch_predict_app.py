from flask import Flask, send_file, render_template, request, jsonify
from flask_bootstrap import Bootstrap
from pitch_predict_api import generateStatsForPlayer, stacked, features, predict_2019

import pickle
import numpy as np
import pandas as pd
import psycopg2 as pg
import pandas.io.sql as pd_sql
import os

from bokeh.io import output_file, show
from bokeh.embed import components, file_html
from bokeh.models import CategoricalColorMapper, HoverTool, Legend
from bokeh.core.properties import value
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.resources import CDN

app = Flask(__name__)
Bootstrap(app)

connection_args = {'host': 'localhost', 'dbname': 'mlb', 'port': 5432}
connection = pg.connect(**connection_args)

@app.route('/', methods=['GET', 'POST'])
def homescreen():
    # player = request.form[playername]
    return render_template("homepage.html")


@app.route('/api/stats/<player>')
def displayStatsForPlayer(player):
    return jsonify(generateStatsForPlayer(player))

@app.route('/player', methods=["POST", "GET"])
def playerPage():
    player = request.args.get('name')
    last_name = player.split()[1]

    query4 = "SELECT * FROM combined WHERE name = '%s'" % player

    at_bats = pd_sql.read_sql(query4, connection)
    pitcher_id = at_bats.pitcher_id[1]
    link = "https://securea.mlb.com/mlb/images/players/head_shot/" + str(pitcher_id) + ".jpg"

    stats = generateStatsForPlayer(player)
    ft = features(player)

    X = [ft]

    inj_prob = predict_2019(X)

    script, div = stacked(player)

    return render_template("profilepage.html", player=player, link=link, stats=stats, script=script, div=div, prob=inj_prob, last_name=last_name)

if __name__ == '__main__':
    app.run()
