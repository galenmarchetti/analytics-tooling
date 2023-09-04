import streamlit as st
import pandas as pd
import altair as alt
from datetime import time

st.set_page_config(layout="wide")

story_df = pd.read_csv('recent_comment_velocity_df.csv')
comment_df = pd.read_csv('comment_timeseries_df.csv')

story_df = story_df[
    [ "comments_per_minute",
     "recent_comments_per_minute",
    "time_since_post", 
     "num_comments",
     "title", 
     "url", ]]

story_df_with_selections = story_df.copy()
story_df_with_selections.insert(0, "Select", False)

#st.dataframe(story_df_with_selections)

max_time_slider_value = time.max
### Slider for user to filter for recency
start_time = st.slider("Only show stories published within the last: ",
                value=time.max,
                format="H[h]m[m]"
            )

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
                x='comment_timestamp:T',
                y='cumulative_count:Q',
                color='story_title:N',
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
                alt.X('comment_timestamp:T'),
                alt.Y('count(*):Q').title('Comments per hour'),
                color='story_title:N',
        ))

    st.altair_chart(comment_velocity_chart, use_container_width=True)