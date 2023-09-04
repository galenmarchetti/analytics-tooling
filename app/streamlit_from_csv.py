import streamlit as st
import pandas as pd
import altair as alt
from datetime import time, datetime, timedelta
import pytz

st.set_page_config(layout="wide")

comment_timeseries_csv_filename = 'comment_timeseries_0.1.csv'
stories_csv_filename = 'stories_0.1.csv'

story_parse_dates = ['story_datetime']
comment_parse_dates = ['comment_timestamp']
story_df = pd.read_csv(stories_csv_filename, parse_dates=story_parse_dates)
comment_df = pd.read_csv(comment_timeseries_csv_filename, parse_dates=comment_parse_dates)

### TODO TODO TODO FIGURE OUT HOW TO GET COMMENT VELOCITY IN SMALLER INTERVALS
### TODO TODO TODO COUNT COMMENTS BY ID NOT BY TIMESTAMP

if 'datetime_now' not in st.session_state:
    st.session_state['datetime_now'] = datetime.now().astimezone(pytz.utc)

story_df['time_since_post'] = story_df['story_datetime'].apply(
    lambda dt: st.session_state['datetime_now'] - dt
)

### Slider for user to filter for calculating recent comment velocity
comment_velocity_recency_filter = st.slider("Calculate comment velocity based on comments published within the last: ",
                min_value=time(0,15),
                value=time(1,30),
                max_value=time(23,45),
                format="H[h]m[m]",
                step=timedelta(minutes=15)
)

comment_recency_timedelta = timedelta(
    minutes=comment_velocity_recency_filter.hour * 60 + comment_velocity_recency_filter.minute
)

comment_velocity_calculator = comment_df[
    comment_df['comment_timestamp'] > \
        st.session_state['datetime_now'] - comment_recency_timedelta
]

recent_comment_metrics = comment_velocity_calculator.groupby(
        ['story_id']
    ).agg(
        {
            'comment_timestamp': ['min', 'count'],
        }
    )

# groupby / agg with multiple aggs gives a multindex, need to drop a level to join
recent_comment_metrics.columns = recent_comment_metrics.columns.droplevel(0)
recent_comment_metrics = recent_comment_metrics.rename(
    {'min': 'earliest_recent_comment_timestamp', 'count': 'num_recent_comments'},
    axis=1
)

#recent_comment_metrics
story_df_with_comment_metrics = story_df.merge(recent_comment_metrics, on=['story_id'])

story_df_with_comment_metrics['td_since_earliest_recent_comment'] = (
    st.session_state['datetime_now'] - 
     story_df_with_comment_metrics['earliest_recent_comment_timestamp']
)
story_df_with_comment_metrics['minutes_since_earliest_recent_comment'] = (
    story_df_with_comment_metrics['td_since_earliest_recent_comment'].apply(
        lambda x: x.total_seconds() / 60
    )
)

story_df_with_comment_metrics['comments_per_min'] = (
    story_df_with_comment_metrics['num_recent_comments'] * 1.0 /
    story_df_with_comment_metrics['minutes_since_earliest_recent_comment']
)

story_df_with_selections = story_df_with_comment_metrics.copy()
story_df_with_selections.insert(0, "Select", False)

story_df_with_selections = story_df_with_selections[[
    'Select',
    'comments_per_min',
    'title',
    'num_comments',
    'time_since_post',
    'url'
]]

# Get dataframe row-selections from user with st.data_editor
edited_df = st.data_editor(
        story_df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=story_df.columns,
        use_container_width=True,
)

# Filter the dataframe using the temporary column, then drop the column
selected_rows = edited_df[edited_df.Select]
selected_rows.drop('Select', axis=1)
if len(selected_rows) > 0:
    stories = list(selected_rows['title'].unique())
else:
    stories = None

#unique_story_titles = list(comment_df['story_title'].unique())
#stories = st.multiselect("Choose stories to analyze:",
#                         unique_story_titles)

if not stories:
    st.error("Please select at least one story.")
else:
    filtered_comment_df = comment_df[comment_df['story_title'].isin(stories)]

    cumulative_chart = (alt.Chart(filtered_comment_df)
            .transform_window(
                groupby=['story_title'],
                sort=[{'field': 'comment_timestamp'}],
                frame=[None, 0],
                cumulative_count='count(*)'
            )
            .mark_line(
                interpolate='monotone'
            )
            .encode(
                alt.X('comment_timestamp').title("Time"),
                alt.Y('cumulative_count:Q').title("Total Comments"),
                alt.Color('story_title:N').title("Title")
        ))

    st.altair_chart(cumulative_chart, use_container_width=True)

    comment_velocity_chart = (alt.Chart(filtered_comment_df)
            .transform_timeunit(
                comment_timestamp='yearmonthdatehours(comment_timestamp)'
            )
            .mark_line(
                interpolate='monotone'
            )
            .encode(
                alt.X('comment_timestamp').title("Time"),
                alt.Y('count(*):Q').title('Comments per hour'),
                alt.Color('story_title:N').title("Title")
        ))

    st.altair_chart(comment_velocity_chart, use_container_width=True)