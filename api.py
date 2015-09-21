"""
SRL API wrapper

Module to search for races of specific 
games from the SpeedRunsLive public API
"""

import urllib.request
import urllib.error
import datetime as dt
import re
import json
import math
import random
from time import time

debugging = True

if debugging:
    import displayinfo

def grab(game, goal_string=None, start_date=dt.datetime(2009,1,1), end_date=dt.datetime.now(), weekdays=None):
    """
    Main search function for SpeedRunsLive API
    Searches the API for races in the given game
    Optional search for specific goals, date range and weekdays (for weekly races)
    Converts dates from UTC timestamps to Python datetimes for comparison
    Limits list to 999 races for sqlite purposes
    Returns a list of races that match the given parameters
    """

    PAGE_SIZE = 1000

    baseurl = 'http://api.speedrunslive.com:81/pastraces?game=' + game + '&pageSize=' + str(PAGE_SIZE)
    races = []

    if goal_string:
        goal = re.compile("^"+goal_string+"$")
    else:
        goal = re.compile('\S')
    
    page_info = get_page(baseurl)

    #quit out if page not found
    if page_info == 0 or page_info['count'] == 0:
        print("Error: game not found!")
        print("Make sure you're using the game abbreviation and not the full name")
        return

    #Get info for pagination
    count = page_info['count']-1
    last_page = math.ceil(count/500)
    current_page = 1

    #Begin API search
    while True:
        too_far = False

        for i in range(PAGE_SIZE):
            try:
                race = page_info['pastraces'][i]

                race_date = get_datetime(race)
                if race_date >= start_date:
                    if race_date > end_date:
                        continue
                    if goal.match(race['goal'].lower()):

                        #check for weekly
                        if weekdays:
                            if race_date.weekday() in weekdays:
                                #print('weekday match found!')
                                races.append(race)
                        else:
                            #print('race found!')
                            races.append(race)
                else:
                    too_far = True
                    break
            except IndexError as e:
                too_far = True
                break

        if too_far:
            print('out of races to search!')
            break

        if current_page == last_page:
            break
        elif len(races) > 999:
            print('race list too big! cutting off at', races[998]['id'])
            break
        else:
            current_page += 1
            page_info = get_page(baseurl + '&page=' + str(current_page))

    if debugging:
        display_races(races)

    return races[:999]

def grab_nearby(race_date, game):
    """
    Search API for all races in game that a week before or after given date
    Use for correcting false positive in weekly searchs
    Returns list of races within 2 week span
    """

    from_date = dt.datetime.fromtimestamp(race_date-604800)
    to_date = dt.datetime.fromtimestamp(race_date+604800)
    return grab(game, None, start_date=from_date, end_date=to_date)

def grab_single(id):
    """
    Grab a single race from given race ID string
    Returns list containing one race
    """

    baseurl = 'http://api.speedrunslive.com:81/pastraces?id='

    pageurl = baseurl + id
    page_info = get_page(pageurl)

    if page_info == 0:
        print('Unable to grab race id: ', id)

    return [page_info['pastraces'][0]]

def grab_comments(player):
    """
    Grab every race comment from player up to 2500 races
    """

    baseurl = 'http://api.speedrunslive.com:81/pastraces?player=' + player + '&pageSize=2500'

    #get all player comments
    page_info = getPage(baseurl)
    count = page_info['count']
    for i in range(count):
        results = page_info['past_races'][i]['results']
        
        for result in results:
            if result['player'].lower() == player:
                if result['message']:
                    comments.append(result['message'])
                    break

    return comments

def grab_random_comments(player, amount=3):
    """
    Grabs a 1-10 of comments at random for player
    """

    comments = grab_comments(player)

    #limit to 10 comments
    if amount < 1 or amount > 10:
        amount = 1

    random_comments = []
    for i in range(amount):
        random_comments.append(random.choice(comments))

    for comment in random_comments:
        print(player + ":", comment)

    return comments

def get_page(pageurl):
    """
    Requests page from pageurl
    Returns deserialized json dict, or 0 if error occurred
    """

    print('Getting page', pageurl)
    try:
        page = urllib.request.urlopen(pageurl)
        pageJSON = page.read().decode('utf-8')
        page_info = json.loads(pageJSON)

    except urllib.error.HTTPError as e:
        print("HTTPError occured with page")
        page_info = 0
    except urllib.error.URLError as e:
        print("URLError occured with page")
        page_info = 0

    return page_info

def display_races(races, results=False, limit=16):
    """
    Display list of races in console for debugging
    """

    for race in races:
        racedate = get_datetime(race)
        displayinfo.align(race['id'], str(racedate) + str(racedate.weekday()), race['game']['abbrev'], race['goal'], limit=limit)
        if results:
            display_results(race)

def display_results(*races):
    """
    Display results from race for debugging
    """

    for race in races:
        results = race['results']
        displayinfo.alignheader('place', 'player', 'time', 'msg', limit=16)
        for result in results:
            place = result['place']
            if place == 9999:
                place = ''
                result['time'] = 'DQ'
            elif place == 9998:
                place = ''
                result['time'] = 'Quit'
            
            displayinfo.align(place, result['player'], convert_time(result['time']), result['message'], limit=16)
        print('\n')

def get_datetime(race):
    """
    Returns datetime object for date of race
    """
    return dt.datetime.utcfromtimestamp(int(race['date']))

def convert_time(racetime):
    """
    Converts time in seconds to hh:mm:ss for display
    """

    if racetime == 'DQ' or racetime == 'Quit':
        return racetime
    elif racetime > 3599:
        hh = math.floor(racetime/3600)
        mm = math.floor((racetime-(3600*hh))/60)
        ss = racetime-((3600*hh)+(60*mm))
    elif racetime > 59:
        hh = 0
        mm = math.floor(racetime/60)
        ss = (racetime-(60*mm))
    else:
        hh = 0
        mm = 0
        ss = racetime

    formattedtime = "%02d:%02d:%02d" % (hh, mm, ss)
    return formattedtime