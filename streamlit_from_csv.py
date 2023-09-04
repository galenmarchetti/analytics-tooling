import streamlit as st
import pandas as pd
import altair as alt
from datetime import time, datetime, timedelta

st.set_page_config(layout="wide")

story_parse_dates = ['story_datetime']
comment_parse_dates = ['comment_timestamp']
story_df = pd.read_csv('recent_comment_velocity_df.csv', parse_dates=story_parse_dates)
comment_df = pd.read_csv('comment_timeseries_df.csv', parse_dates=comment_parse_dates)

story_df = story_df[
    ["comments_per_minute",
     "recent_comments_per_minute",
     "num_comments",
     "title", 
     "url",
     "story_datetime"]]

#st.write("Story dataframe types: ", story_df.dtypes)

if 'datetime_now' not in st.session_state:
    st.session_state['datetime_now'] = datetime.now()

story_df['time_since_post'] = story_df['story_datetime'].apply(
    lambda dt: st.session_state['datetime_now'] - dt
)

story_df_with_selections = story_df.copy()
story_df_with_selections.insert(0, "Select", False)


#st.dataframe(story_df_with_selections)

max_time_slider_value = time.max
### Slider for user to filter by story publish date
story_recency_time_filter = st.slider("Only show stories published within the last: ",
                value=time.max,
                format="H[h]m[m]"
)

### Slider for user to filter for calculating recent comment velocity
comment_velocity_recency_filter = st.slider("Calculate comment velocity based on comments published within the last: ",
                value=time.max,
                format="H[h]m[m]"
)

comment_recency_timedelta = timedelta(
    minutes=comment_velocity_recency_filter.hour * 60 + comment_velocity_recency_filter.minute
)

comment_velocity_calculator = comment_df[
    comment_df['comment_timestamp'] > \
        st.session_state['datetime_now'] - comment_recency_timedelta
]

comment_velocity_per_story = comment_velocity_calculator.groupby(
        ['story_id']
    ).agg(
        {
            'comment_timestamp': ['min', 'count'],
        }
    )

### TODO TODO TODO USE THE ABOVE AGGREGATIONS TO CALCULATE COMMENTS PER MINUTE
### TODO TODO TODO JOIN TO STORY DISPLAY BY STORY ID

story_recency_timedelta = timedelta(
    minutes=story_recency_time_filter.hour * 60 + story_recency_time_filter.minute
)

story_df_with_selections = story_df_with_selections[
    story_df_with_selections['time_since_post'] < story_recency_timedelta  
]

# Get dataframe row-selections from user with st.data_editor
edited_df = st.data_editor(
        #story_df_with_selections,
        story_df_with_selections.drop(['story_datetime'], axis=1),
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
                alt.X('comment_timestamp:T').title("Time"),
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
                alt.X('comment_timestamp:T').title("Time"),
                alt.Y('count(*):Q').title('Comments per hour'),
                alt.Color('story_title:N').title("Title")
        ))

    st.altair_chart(comment_velocity_chart, use_container_width=True)