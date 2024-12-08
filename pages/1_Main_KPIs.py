import pandas as pd
import numpy as np
import pickle
import streamlit as st
import geopandas as gpd
import plotly.express as px
from utils import *
import json
import streamlit as st
import datetime

# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import firestore
# import requests

st.set_page_config(page_title = 'Main KPIs', page_icon = '📊', layout = 'wide')

st.markdown("## Main KPIs")
# st.sidebar.header("Plotting Demo")
# Add version info and last update time
# st.sidebar.markdown("---")
st.sidebar.markdown("**Version:** 1.0.0")
st.sidebar.markdown(f"**Last Updated:** {datetime.datetime.now().strftime('%Y-%m-%d')}")

brand_list = ['fontvella', 'viladrau', 'cabreiroa', 'vichy', 'lanjaron', 'bezoya', 'veri', 'aquabona', 'solan', 'evian', 'ribes', 'boix', 'aquarel', 'perrier', 'fonter', 'aquafina', 'fontagudes', 'aquadeus', 'casera', 'santaniol', 'cocacola']

# Load local data for testing mode as firebase has 50K queried documents/day limit
with open("./Data/df_docs.pkl", "rb") as file:
    df_docs = pickle.load(file)

df_docs.rename({"post_code":"COD_POSTAL"},axis=1, inplace=True)
df_docs["danone_share"] = round(df_docs["danone_share"],2)

# Competitor info load
with open('./Data/competitor_danone_labels_dict.json', 'r') as json_file:
    competitor_danone_labels_dict = json.load(json_file)

# External Info: gross salary
gross_salary_postcode_df = pd.read_csv("./Data/renta_barcelona.csv", sep=";", decimal=",")
gross_salary_postcode_df['Cat_avg_Gross_Income'] = pd.qcut(gross_salary_postcode_df['Average Gross Income'], q=3, labels=['Low', 'Medium', 'High'])
gross_salary_postcode_df['Cat_avg_Disposable_Income'] = pd.qcut(gross_salary_postcode_df['Average Disposable Income'], q=3, labels=['Low', 'Medium', 'High'])

# Post codes geojson load
gdf_post_code = gpd.read_file('./Data/BARCELONA.geojson', columns=["COD_POSTAL", "geometry"])

gdf_post_code = gdf_post_code.merge(
    gross_salary_postcode_df,
    on=["COD_POSTAL"],
    how="inner"
)

# merge post codes and detections
variables_list = list(df_docs.columns.intersection(brand_list))

post_code_data  = df_docs.drop(["store_type","store_name","shelf id"],axis=1).groupby("COD_POSTAL").sum().reset_index()

gdf_post_code = gdf_post_code.merge(post_code_data, 
                                    on="COD_POSTAL", 
                                    how="left")

danone_shelf_share = (df_docs["total_danone"] / df_docs["total_bottles"]).mean()
non_danone_shelf_share = (df_docs["total_non_danone"] / df_docs["total_bottles"]).mean()
reminder_share = 1 - (float(danone_shelf_share) + float(non_danone_shelf_share))

correlations = {var: gdf_post_code ["Average Gross Income"].corr(gdf_post_code [var]) for var in variables_list}
correlations_df = pd.DataFrame(list(correlations.items()), columns=["Variable", "Correlation"]).round(2)
podium_df = pd.DataFrame({
"Product": df_docs[variables_list].sum().index,
"Share": (df_docs[variables_list].sum().values / df_docs["total_bottles"].sum() * 100).round(1),
"Category": [competitor_danone_labels_dict[col] for col in variables_list]})

col1_1, col1_2, col1_3 = st.columns(3)
    
with col1_1:
        st.plotly_chart(plot_gauge_from_scalar(danone_shelf_share.round(2), "Danone Shelf Share"))
    
with col1_2:
        st.plotly_chart(plot_gauge_from_scalar(non_danone_shelf_share.round(2), "Competitor Shelf Share"))

with col1_3:
        st.plotly_chart(plot_gauge_from_scalar(reminder_share, "Bottles Shelf Share"))

# Create two columns of equal width
col4, col5 = st.columns(2)

with col4:
    st.header("Correlation of Income with Market Share",divider="grey")
    plot_correlation(correlations_df)

with col5:
    st.header("Product Share by Category",divider="grey")
    plot_competitor_share(podium_df)

st.header("Geographical Distribution of Danone Share",divider="grey")
plot_danone_share_map(gdf_post_code)
