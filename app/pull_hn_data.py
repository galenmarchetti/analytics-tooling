import requests as r
from requests.adapters import HTTPAdapter, Retry
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd

### TODO TODO TODO CENTRALIZE FILENAME INTO ONE CONSTANT FOLDER

'''
All HN API requests are constructed using the following reference: https://github.com/HackerNews/API
'''

MAX_TIMEDELTA_TO_PULL_IN_HOURS = 3

base_url = "https://hacker-news.firebaseio.com/v0/"
human_display_item_url = "https://news.ycombinator.com/item?id="
new_stories_slug = "newstories"
item_slug = "item/"
json_append_slug = ".json"

comment_timeseries_csv_filename = 'comment_timeseries_0.1.csv'
stories_csv_filename = 'stories_0.1.csv'

# returns datetime.timedelta object representing time between execution and story posting
def get_td_from_story(story):
    story_unix_time = story['time']
    story_datetime = datetime.fromtimestamp(story_unix_time)
    timedelta_since_post = datetime.now() - story_datetime
    return timedelta_since_post

def get_comments_per_minute_from_story(timedelta_since_post, num_comments):
    minutes_since_post = timedelta_since_post.seconds / 60
    comments_per_minute = (num_comments * 1.0) / minutes_since_post
    return comments_per_minute

def format_timedelta(timedelta_since_post):
    hours_since_post, remainder = divmod(timedelta_since_post.seconds, 3600)
    minutes_since_post, seconds = divmod(remainder, 60)
    time_since_post = str(hours_since_post) + 'h' + str(minutes_since_post) + 'm'
    return time_since_post

def get_comment_timestamps(story_json, delay_in_seconds):
    comments = story_json['kids']
    comment_timestamps = []
    for comment_id in comments:
        comment_response = r.get(base_url + item_slug + str(comment_id) + json_append_slug)
        comment = comment_response.json()
        comment_timestamps.append(comment['time'])
        time.sleep(delay_in_seconds)
    return comment_timestamps

def get_item_timestamps_for_all_kids(item_json, delay_in_seconds):
    if 'kids' not in item_json:
        return []
    kids = item_json['kids']
    kid_timestamps = []
    for kid_id in kids:
        kid_response = r.get(base_url + item_slug + str(kid_id) + json_append_slug)
        kid_json = kid_response.json()
        if not kid_json:
            continue
        if 'time' not in kid_json:
            continue
        kid_timestamp = datetime.fromtimestamp(kid_json['time'])
        if (datetime.now() - kid_timestamp) > timedelta(hours=MAX_TIMEDELTA_TO_PULL_IN_HOURS):
            continue
        kid_timestamps.append(kid_json['time'])
        kid_timestamps = kid_timestamps + get_item_timestamps_for_all_kids(kid_json, delay_in_seconds)
        time.sleep(delay_in_seconds)
    return kid_timestamps

### Get Story IDs for the newest stories from the HN New Stories endpoint
new_stories_response = r.get(base_url + new_stories_slug + json_append_slug)
new_stories_json = new_stories_response.json()
num_stories = len(new_stories_json)

story_records = []
comment_timeseries_records = []
for i, story_id in enumerate(new_stories_json):
    story_response = r.get(base_url + item_slug + str(story_id) + json_append_slug)
    story = story_response.json()
    if not story:
        continue
    if 'descendants' in story:
        num_comments = story['descendants']
    elif ('dead' in story and story['dead']):
        continue
    elif ('deleted' in story and story['deleted']):
        continue
    else:
        raise Exception("Couldn't find descendants in story: " + str(story))
    title = story['title']

    story_unix_time = story['time']
    story_datetime = datetime.fromtimestamp(story_unix_time)
    
    timedelta_since_post = get_td_from_story(story)
    if timedelta_since_post > timedelta(hours=MAX_TIMEDELTA_TO_PULL_IN_HOURS):
        continue
    comments_per_minute = get_comments_per_minute_from_story(timedelta_since_post, num_comments)
    time_since_post = format_timedelta(timedelta_since_post)
    if num_comments > 0:
        item_timestamps = get_item_timestamps_for_all_kids(story, 0.1)
    else:
        item_timestamps = []
    for timestamp in item_timestamps:
        timestamp_dt = datetime.fromtimestamp(timestamp).astimezone(pytz.utc)
        comment_timeseries_records.append({'story_id': story_id, 
                                           'story_title': title, 
                                           'comment_timestamp': timestamp_dt})
        
    story_records.append({
        'story_id': story_id,
        'num_comments': num_comments,
        'title': title,
        'timedelta_since_post': timedelta_since_post,
        'time_since_post': time_since_post,
        'comments_per_minute': comments_per_minute,
        'story_datetime': story_datetime.astimezone(pytz.utc),
        'url': human_display_item_url + str(story_id),
        'comment_timestamps': item_timestamps,
    })
    print("Pulled info for story " + str(i) + "/" + str(num_stories))

comment_timeseries_df = pd.DataFrame.from_records(comment_timeseries_records)
comment_timeseries_df.to_csv(comment_timeseries_csv_filename)

stories_df = pd.DataFrame.from_records(story_records)
stories_df.to_csv(stories_csv_filename)
