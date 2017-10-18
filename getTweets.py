#!/usr/bin/env python

import ConfigParser
import argparse
import os
import sys
import json
import datetime
from dateutil.parser import parse
from datetime import timedelta
from pytz import timezone
import twitter

#######################
#TODO:
#Clean up code
#Error handling
#######################

def jdefault(o):
    return o.__dict__

def main():
    #parsing arguments and setting application flags
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--all', help='delete all tweets even persistent', action='store_true')
    parser.add_argument('-d', '--debug', help='turn debug mode on', action='store_true')
    parser.add_argument('-t', '--tiempo', help='horas de gracia', type=int)
    args = parser.parse_args()
    debugMode = False
    deleteAll = False
    horasdegracia = 0
    if args.all:
        deleteAll = True
        print('deleting all statuses including tagged with persistence...')
    if args.debug:
        debugMode = True
        print('debug mode on (nothing will be deleted)...')
    if args.tiempo:
        horasdegracia = args.tiempo
        print('deleting everything before T-{} hours...'.format(horasdegracia))

    #Reading configuration files
    try:
        sys.stdout.write('reading config file... ')
        config = ConfigParser.RawConfigParser()
        config.read('.twconfig')
        print('success!')
    except:
        print('failed to read config file!')
        exit()

    #Set up API connection
    try:
        sys.stdout.write('connecting to api... ')
        api = twitter.Api(consumer_key=config.get('keys', 'consumer_key'),
                          consumer_secret=config.get('keys', 'consumer_secret'),
                          access_token_key=config.get('keys', 'access_key'),
                          access_token_secret=config.get('keys', 'access_secret'),
                          input_encoding=None, sleep_on_rate_limit=True)
        print('success!')
    except:
        print('failed to connect to twitter api!')
        exit()

    #Tweets containing this char in the body will be skipped 
    persistence = unichr(int(config.get('twitter', 'persistence'), 16))
    print('persistence tag: ' + persistence)
    with open('keep.txt') as fh:
        keeplist = fh.read().splitlines()
    print(keeplist)

    #Getting tweets
    try:
        sys.stdout.write('fetching last 200 statuses... ')
        statuses = api.GetUserTimeline(count=200)
        print('success!')
        print(str(len(statuses)) + ' statuses loaded')
    except:
        print('failed to get statuses!')
        exit()

    if debugMode:
        path = str(os.path.expanduser('~')) + '/debugPath/'
    else:
        path = str(os.path.expanduser('~')) + '/archivingPath/'
    filename = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y%m%d")

    #Handling time difference
    ahorita = datetime.datetime.now(timezone('UTC'))
    delbefore = ahorita - timedelta(hours=horasdegracia)

    #Deleting
    try:
        print('writing to file ' + path + filename + '.txt... ')
        with open(path + filename + '.txt', 'a') as outfile:
            for status in statuses:
                statusparsed = json.loads(str(status).encode())
                sys.stdout.write(statusparsed['text'] + ' - ')
                tweettime = parse(statusparsed['created_at'])
                print(tweettime)
                if tweettime < delbefore:
                    if deleteAll:
                        outfile.write(json.dumps(status, default=jdefault) + '\n')
                        if debugMode:
                            print('deleted! (not really)')
                        else:
                            api.DestroyStatus(statusparsed['id'])
                            print('deleted! (-a)')
                    else:
                        if statusparsed['id_str'] not in keeplist and persistence not in statusparsed['text']: 
                            outfile.write(json.dumps(status, default=jdefault) + '\n')
                            if debugMode:
                                print('deleted! (not really)')
                            else:
                                api.DestroyStatus(statusparsed['id'])
                                print('deleted!')
                        else:
                            print('skipped!')
                else:
                    print('skipped!')
    except:
        print('failed writing to file!')
        exit()

if __name__ == "__main__":
    main()
