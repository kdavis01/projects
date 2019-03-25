import numpy as np
import pandas as pd
import csv
from collections import OrderedDict

def make_dict():

    tweet_dict = OrderedDict()

    with open('twcs.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            tweet_id = row[0]
            tweet_dict[tweet_id] = {'tweet_id': row[0], 'author_id': row[1], 'response_tweet_id': row[5], 'in_response_to_tweet_id': row[6], 'text': row[4]}

    return tweet_dict

def group_conversations(dt):

    all_convos = []
    id_set = set()

    for tweet_id, values_dict in dt.items():

        if tweet_id in id_set:
            continue

        convo = []

        # find all tweets connected to first tweet
        convo.append(str(tweet_id))

        resp = values_dict['response_tweet_id']

        if not resp == '0':

            responses = resp.split(',')
            [convo.append(i) for i in responses]

        resp_to = values_dict['in_response_to_tweet_id']

        if not resp_to == '0':

            responded_to = resp_to.split(',')
            [convo.append(i) for i in responded_to]

        # loop through tweets in convo and find all of their connections
        i = 0
        while i < len(convo):

            try:
                resp = dt[convo[i]]['response_tweet_id']
                resp_to = dt[convo[i]]['in_response_to_tweet_id']


                if not resp == '0':
                    r = resp.split(',')
                    for num in r:
                        if not num in convo:
                            convo.append(num)

                if not resp_to == '0':
                    rt = resp_to.split(',')
                    for num in rt:
                        if not num in convo:
                            convo.append(num)

                id_set.add(convo[i])

                i+=1

            except:
                convo.remove(convo[i])

        all_convos.append(convo)

    return all_convos
