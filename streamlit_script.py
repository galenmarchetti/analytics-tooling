import requests as r
import time
from datetime import datetime
from datetime import timedelta
import streamlit as st
import pandas as pd
import altair as alt

'''
All HN API requests are constructed using the following reference: https://github.com/HackerNews/API
'''

base_url = "https://hacker-news.firebaseio.com/v0/"
human_display_item_url = "https://news.ycombinator.com/item?id="
new_stories_slug = "newstories"
item_slug = "item/"
json_append_slug = ".json"

### Get Story IDs for the newest stories from the HN New Stories endpoint
new_stories_response = r.get(base_url + new_stories_slug + json_append_slug)
new_stories_json = new_stories_response.json()

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
    print("Total number of timestamps we're getting: " + str(len(comments)))
    comment_timestamps = []
    for comment_id in comments:
        comment_response = r.get(base_url + item_slug + str(comment_id) + json_append_slug)
        comment = comment_response.json()
        comment_timestamps.append(comment['time'])
        time.sleep(delay_in_seconds)
    return comment_timestamps

# Structure: story_id: {num_comments, }
story_info_tracker = {}
num_stories = len(new_stories_json)
for i, story_id in enumerate(new_stories_json):
    story_response = r.get(base_url + item_slug + str(story_id) + json_append_slug)
    story = story_response.json()
    if 'descendants' in story:
        num_comments = story['descendants']
    elif ('dead' in story and story['dead']):
        continue
    else:
        raise Exception("Couldn't find descendants in story: " + str(story))
    title = story['title']
    timedelta_since_post = get_td_from_story(story)
    comments_per_minute = get_comments_per_minute_from_story(timedelta_since_post, num_comments)
    time_since_post = format_timedelta(timedelta_since_post)
    if num_comments > 0:
        print("Pulling comment info for story with " + str(num_comments) + " comments")
        comment_timestamps = get_comment_timestamps(story, 0.1)
    else:
        comment_timestamps = []
    story_info_tracker[story_id] = {
        'num_comments': num_comments,
        'title': title,
        'timedelta_since_post': timedelta_since_post,
        'time_since_post': time_since_post,
        'comments_per_minute': comments_per_minute,
        'url': human_display_item_url + str(story_id),
        'comment_timestamps': comment_timestamps,
    }
    print("Pulled info for story " + str(i) + "/" + str(num_stories))
    if i == 25:
        break


# Gets comments per minute from an array of unix timestamps representing comment times, and minutes in the past to consider recent.
def get_comments_per_minute_from_recent_comments(comment_unix_timestamp_array, minutes_to_consider_recent):
    recency_datetime = datetime.now() - timedelta(minutes=minutes_to_consider_recent)
    filtered_comments = [comment for comment in comment_unix_timestamp_array if comment >= recency_datetime.timestamp()]
    filtered_comments_sorted = sorted(filtered_comments)
    if len(filtered_comments_sorted) <= 1:
        return 0
    first_comment_timestamp = datetime.fromtimestamp(filtered_comments_sorted[0])
    last_comment_timestamp = datetime.fromtimestamp(filtered_comments_sorted[-1])
    timedelta_between_first_last_comment = last_comment_timestamp - first_comment_timestamp
    minutes_between_first_last_comment = (timedelta_between_first_last_comment.seconds * 1.0) / 60
    return (len(comment_unix_timestamp_array) * 1.0) / minutes_between_first_last_comment

def get_stories_with_recent_comment_velocity(stories, recency_in_minutes):
    stories_with_recent_comment_velocity = {}
    for story_id, story in stories.items():
        recent_comment_velocity = get_comments_per_minute_from_recent_comments(story['comment_timestamps'], recency_in_minutes)
        story['recent_comments_per_minute'] = recent_comment_velocity
        stories_with_recent_comment_velocity[story_id] = story
    return stories_with_recent_comment_velocity

def convert_sorted_stories_to_display_list(sorted_stories):
    original_list = [sorted_story[1] for sorted_story in sorted_stories]
    display_list = []
    for story in original_list:
        display_story = story.copy()
        if 'comment_timestamps' in display_story:
            del display_story['comment_timestamps']
            del display_story['timedelta_since_post']
        display_list.append(display_story)
    return display_list

def get_recent(sorted_stories_display_list, minutes_to_consider_recent):
    return [sorted_story for sorted_story in sorted_stories_display_list \
            if (sorted_story['timedelta_since_post'].seconds / 60) < minutes_to_consider_recent]


###
###
###

## EDIT THIS TO CHANGE DEFINITION OF "RECENT COMMENT"
MINUTES_TO_CONSIDER_RECENT = 120


###
###
###

## SORT AND FORMAT STORIES BY RELEVANT METRICS

story_info_tracker = get_stories_with_recent_comment_velocity(story_info_tracker, MINUTES_TO_CONSIDER_RECENT)

num_comments_sorted_stories = sorted(story_info_tracker.items(), key=lambda x: x[1]['num_comments'], reverse=True)
comment_velocity_sorted_stories = sorted(story_info_tracker.items(), key=lambda x: x[1]['comments_per_minute'], reverse=True)
recent_comment_velocity_sorted_stories = sorted(story_info_tracker.items(), key=lambda x: x[1]['recent_comments_per_minute'], reverse=True)

num_comments_sorted_stories_display = convert_sorted_stories_to_display_list(num_comments_sorted_stories)
comment_velocity_sorted_stories_display = convert_sorted_stories_to_display_list(comment_velocity_sorted_stories)
recent_comment_velocity_sorted_stories_display = convert_sorted_stories_to_display_list(recent_comment_velocity_sorted_stories)

comment_velocity_df = pd.DataFrame.from_records(comment_velocity_sorted_stories_display)

st.dataframe(comment_velocity_df)
