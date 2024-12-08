import streamlit as st
import datetime

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
    layout="wide",
)

st.write("# Welcome to Bottle Vision Dashboard! 👋")


st.markdown("""
This dashboard provides real-time analysis of bottle placement and market share across locations.

### Purpose
- Monitor Danone's shelf presence vs competitors
- Track geographical coverage of products
- Analyze market share correlations with demographic data

### How to Use
1. **Main KPIs Tab**
   - View overall shelf share metrics
   - Analyze income correlations
   - Explore geographical distribution

2. **Granular KPIs Tab**
   - Select specific postal codes for detailed analysis
   - Compare brand performance
   - View detailed geographical breakdowns

""")

# Add version info and last update time
st.sidebar.markdown("**Version:** 1.0.0")
st.sidebar.markdown(f"**Last Updated:** {datetime.datetime.now().strftime('%Y-%m-%d')}")