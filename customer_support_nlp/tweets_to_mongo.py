import csv
import json
import pandas as pd
import sys, getopt, pprint
from pymongo import MongoClient

csvfile = open("sample.csv")
reader = csv.DictReader(csvfile)

config = {
  'username': 'mongo_user',
  'password': 'password'
}

client = MongoClient(**config)

db = client.customer_support_tweets

header = ["tweet_id", "author_id", "inbound", "created_at", "text", "response_tweet_id", "in_response_to_tweet_id"]

for line in reader:
    row = {}
    for field in header:
        row[field] = line[field]

    db.tweets.insertOne(row)
