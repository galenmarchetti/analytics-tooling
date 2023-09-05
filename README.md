# analytics-tooling

A Kurtosis package that runs a HN analytics dashboard built in [Streamlit](https://github.com/streamlit/streamlit).

Note that it takes between 6-10 minutes to run right now because it pulls data when it runs, and I want to be kind to the API.

[Install Kurtosis](https://docs.kurtosis.com/install) and then run with:
```
kurtosis run github.com/galenmarchetti/analytics-tooling
```

And then in the output, click on the frontend url at the end:

```
========================================== User Services ==========================================
UUID           Name           Ports                                                       Status
b161fd4d8055   hn-analytics   hn-analytics-frontend: 8501/tcp -> http://127.0.0.1:58824   RUNNING
```
