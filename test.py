import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
    layout="wide",
)
# Set page title
st.title("Dashboard with Column Layout")


# Create sample data
np.random.seed(42)
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
data = {
    'date': dates,
    'values_1': np.random.normal(100, 15, len(dates)),
    'values_2': np.random.normal(50, 10, len(dates)),
    'category': np.random.choice(['A', 'B', 'C', 'D'], len(dates))
}
df = pd.DataFrame(data)

# Create two columns of equal width
col1, col2 = st.columns(2)

# First column visualization
with col1:
    st.subheader("Time Series Chart")
    line_chart = alt.Chart(df).mark_line().encode(
        x='date:T',
        y='values_1:Q',
        tooltip=['date', 'values_1']
    ).properties(height=300)
    st.altair_chart(line_chart, use_container_width=True)

# Second column visualization
with col2:
    st.subheader("Distribution Plot")
    hist_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('values_2:Q', bin=True),
        y='count()',
        tooltip=['count()']
    ).properties(height=300)
    st.altair_chart(hist_chart, use_container_width=True)

# Full-width visualization below
st.subheader("Category Comparison Over Time")
category_chart = alt.Chart(df).mark_area().encode(
    x='date:T',
    y='count():Q',
    color='category:N',
    tooltip=['date', 'category', 'count()']
).properties(height=300)
st.altair_chart(category_chart, use_container_width=True)