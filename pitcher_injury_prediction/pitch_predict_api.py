from flask import Flask, send_file, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
import psycopg2 as pg
import pandas.io.sql as pd_sql
import math

from bokeh.io import output_file, show
from bokeh.embed import components, file_html
from bokeh.models import CategoricalColorMapper, HoverTool, Legend
from bokeh.core.properties import value
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.resources import CDN

connection_args = {'host': 'localhost', 'dbname': 'mlb', 'port': 5432}
connection = pg.connect(**connection_args)

def generateStatsForPlayer(player):

    query = "SELECT * FROM pitch_percentages WHERE Name = '%s'" % player

    pitches = pd_sql.read_sql(query, connection)

    query2 = "SELECT * FROM stats WHERE Name = '%s'" % player

    pitcher_stats = pd_sql.read_sql(query2, connection)
    teams = pitcher_stats.loc[pitcher_stats['year'] != '2019', 'team'].tolist()
    past_teams = set(teams)

    query3 = "SELECT * FROM tommyj WHERE name = '%s'" % player

    surgeries = pd_sql.read_sql(query3, connection)

    query4 = "SELECT * FROM combined WHERE name = '%s'" % player

    at_bats = pd_sql.read_sql(query4, connection)

    statslist =[]
    pastinjurylist = []

    for index, row in pitches.iterrows():
        yeardict = {}
        yeardict['year'] = str(pitches.year[index])
        yeardict['percent_fastball'] = str(pitches.fastball[index])
        yeardict['percent_changeup'] = str(pitches.changeup[index])
        yeardict['percent_curve'] = str(pitches.curve[index])
        yeardict['percent_cutter'] = str(pitches.cutter[index])
        yeardict['percent_splitter'] = str(pitches.splitter[index])
        yeardict['percent_knuckle'] = str(pitches.knuckle[index])
        yeardict['percent_slider'] = str(pitches.slider[index])
        yeardict['percent_sinker'] = str(pitches.sinker[index])

        add_pitches = float(pitches.fastball[index]) + float(pitches.changeup[index]) + float(pitches.curve[index]) + float(pitches.cutter[index]) + float(pitches.splitter[index]) + float(pitches.knuckle[index]) + float(pitches.slider[index]) + float(pitches.sinker[index])
        yeardict['percent_other'] = str(1 - add_pitches)

        statslist.append(yeardict)

        if pitches.injured[index]:
            pastinjurylist.append(str(pitches.year[index]))


    pitchdict = dict.fromkeys(['name', 'age', 'current_team', 'throws', 'past_teams', 'total_innings', 'tommy_john', 'era', 'speed', 'past_injuries', 'stats' ])

    pitchdict['name'] = player
    pitchdict['age'] = str(pitches.age.iloc[-1].replace('.0', ''))
    pitchdict['past_teams'] = str(', '.join(past_teams))
    pitchdict['total_innings'] = str(round(pitcher_stats.innings_pitched.sum(),2))

    if surgeries.empty:
        pitchdict['tommy_john'] = 'None'
    else:
        pitchdict['tommy_john'] = str(surgeries.year.tolist())

    pitchdict['era'] = str(math.floor(pitcher_stats.era.mean()*1000)/1000)
    pitchdict['speed'] = str(math.floor(at_bats.end_speed.mean()*1000)/1000)
    pitchdict['current_team'] = str(teams[0])
    pitchdict['stats'] =  statslist

    if not pastinjurylist:
        pitchdict['past_injuries'] = 'None'
    else:
        pitchdict['past_injuries'] = str(', '.join(pastinjurylist))

    if pitches.lefty[0] == '1':
        pitchdict['throws'] = 'Left'
    else:
        pitchdict['throws'] = 'Right'

    return pitchdict

def stacked(player):

    playerStats = generateStatsForPlayer(player)
    pitch_breakdown = playerStats['stats']

    years = []
    pitches = ['Fastball', 'Changeup', 'Curve', 'Cutter', 'Splitter', 'Knuckle', 'Slider', 'Sinker', 'Other']

    fastballs = []
    changeups = []
    curves = []
    cutters = []
    splitters = []
    knuckles = []
    sliders = []
    sinkers = []
    others =[]

    for item in pitch_breakdown:
        yr = item['year']
        years.append(yr)
        fastballs.append(float(item['percent_fastball']))
        changeups.append(float(item['percent_changeup']))
        curves.append(float(item['percent_curve']))
        cutters.append(float(item['percent_cutter']))
        splitters.append(float(item['percent_splitter']))
        knuckles.append(float(item['percent_knuckle']))
        sliders.append(float(item['percent_slider']))
        sinkers.append(float(item['percent_sinker']))
        others.append(float(item['percent_other']))

    throws = []
    data = { 'Year': years }

    for perc in fastballs:
        if perc != 0:
            throws.append('Fastball')
            data['Fastball'] = fastballs
            break
    for perc in changeups:
        if perc != 0:
            throws.append('Changeup')
            data['Changeup'] = changeups
            break
    for perc in curves:
        if perc != 0:
            throws.append('Curve')
            data['Curve'] = curves
            break
    for perc in cutters:
        if perc != 0:
            throws.append('Cutter')
            data['Cutter'] = cutters
            break
    for perc in splitters:
        if perc != 0:
            throws.append('Splitter')
            data['Splitter'] = splitters
            break
    for perc in knuckles:
        if perc != 0:
            throws.append('Knuckle')
            data['Knuckle'] = knuckles
            break
    for perc in sliders:
        if perc != 0:
            throws.append('Slider')
            data['Slider'] = sliders
            break
    for perc in sinkers:
        if perc != 0:
            throws.append('Sinker')
            data['Sinker'] = sinkers
            break
    for perc in others:
        if perc != 0:
            throws.append('Other')
            data['Other'] = others
            break

    colors = Category20c[len(throws)]

    # return jsonify(data)
    p = figure(x_range=years, plot_height=350, plot_width=800, title="Pitch Breakdown By Year", toolbar_location=None, tools="")
    p.vbar_stack(throws, x='Year', width=0.9, color=colors, source=data, legend=[value(x) for x in throws])

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "center_right"
    p.legend.orientation = "vertical"

    new_legend = p.legend[0]
    p.legend[0].plot = None
    p.add_layout(new_legend, 'right')

    script, div = components(p)

    Flask(__name__).logger.info(script)
    return [script,div]

def features(player):
    query = "SELECT * FROM predict_data WHERE Name = '%s'" % player

    p = pd_sql.read_sql(query, connection)

    features = [float(p.age[0]), float(p.past_surgery[0]), float(p.lefty[0]), float(p.win_percent[0]), float(p.era[0]), float(p.games_played[0]), float(p.h_ip[0]), float(p.bb_ip[0]), float(p.so_ip[0]), float(p.avg_innings_per_game[0]), float(p.avg_batters_per_game[0]), float(p.max_speed[0]), float(p.changeup[0]), float(p.curve[0]), float(p.sinker[0]), float(p.cutter[0]), float(p.fastball[0]), float(p.splitter[0]), float(p.knuckle[0]), float(p.slider[0])]

    return features

with open("svm_model_balanced.pkl", "rb") as f:
    model = pickle.load(f)

def predict_2019(X):
    y_proba = model.predict_proba(X)
    inj_prob = y_proba[0][1]

    inj_prob = math.floor(inj_prob*1000)/1000

    return str(inj_prob)
