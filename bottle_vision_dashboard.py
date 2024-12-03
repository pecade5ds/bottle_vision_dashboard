import pandas as pd
import numpy as np
import pickle
import streamlit as st
import geopandas as gpd
import plotly.express as px
from utils import *
import json

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests

# Config
brand_list = ['fontvella', 'viladrau', 'cabreiroa', 'vichy', 'lanjaron', 'bezoya', 'veri', 'aquabona', 'solan', 'evian', 'ribes', 'boix', 'aquarel', 'perrier', 'fonter', 'aquafina', 'fontagudes', 'aquadeus', 'casera', 'santaniol', 'cocacola']

st.markdown(
    """
    <h1 style="text-align: center;">Bottle Vision Dashboard</h1>
    """, 
    unsafe_allow_html=True
)


# Firebase credentials
# db = firestore.Client.from_service_account_info(st.secrets["firebase"])

# # Config load
# with open('./Data/config/query_config.json', 'r') as json_file:
#     db_schema_name_str = json.load(json_file)["db_schema_name"]

# # Firebase conection
# docs = db.collection(db_schema_name_str).get()

# Preprocessing Firebase info
# df_docs = preprocess_docs(docs, competitor_danone_labels_dict, usecols=["COD_POSTAL", "geometry"])

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

tabs = st.tabs(["Main KPIs", "Granular KPIs"])

with tabs[0]:

    # danone_mkt_share = df_docs["total_danone"].sum() / df_docs["total_bottles"].sum()
    # non_danone_mkt_share = df_docs['total_non_danone'].sum() / df_docs["total_bottles"].sum()
    
    danone_shelf_share = (df_docs["total_danone"] / df_docs["total_bottles"]).mean()
    non_danone_shelf_share = (df_docs["total_non_danone"] / df_docs["total_bottles"]).mean()
    reminder_share = 1 - (float(danone_shelf_share) + float(non_danone_shelf_share))

    col1_1, col1_2, col1_3 = st.columns(3)
    
    with col1_1:
        st.plotly_chart(plot_gauge_from_scalar(danone_shelf_share.round(2), "Danone Shelf Share"), use_container_width=True)
    
    with col1_2:
        st.plotly_chart(plot_gauge_from_scalar(non_danone_shelf_share.round(2), "Competitor Shelf Share"), use_container_width=True)

    with col1_3:
        st.plotly_chart(plot_gauge_from_scalar(reminder_share, "Bottles Shelf Share"), use_container_width=True)
    
    correlations = {var: gdf_post_code ["Average Gross Income"].corr(gdf_post_code [var]) for var in variables_list}
    correlations_df = pd.DataFrame(list(correlations.items()), columns=["Variable", "Correlation"])   
    podium_df = pd.DataFrame({
        "Product": df_docs[variables_list].sum().index,
        "Share": (df_docs[variables_list].sum().values / df_docs["total_bottles"].sum() * 100).round(1),
        "Category": [competitor_danone_labels_dict[col] for col in variables_list]})


    col11, col22 = st.columns([1, 1])  # Dos columnas verticales (de igual tamaño)
    col33 = st.columns(1)  # Una columna horizontal
    
    # Primer gráfico en la primera columna (col1)
    with col11:
        plot_correlation(correlations_df)
    with col22:
        plot_competitor_share(podium_df)
    
    plot_danone_share_map(gdf_post_code)
        

with tabs[1]:
   
    codigos_postales = df_docs['COD_POSTAL'].unique()
    
    df_in = pd.melt(df_docs[df_docs.columns.intersection(list(competitor_danone_labels_dict.keys()) + ["COD_POSTAL"])],
                    id_vars=['COD_POSTAL'],
                    var_name='brand',
                    value_name='value')
    df_in['Category'] = df_in['brand'].map(competitor_danone_labels_dict)
    
    df_in.loc[df_in.Category == "competitor", "value"] = df_in.loc[df_in.Category == "competitor", "value"] * -1

    # Streamlit widget for selecting postal code
    post_code_select = st.selectbox('Post Code:', codigos_postales)
    
    # Filter the data based on the selected post code
    filtered_df = df_in[df_in['COD_POSTAL'] == post_code_select]
    
    # Call your plotting function with the filtered data
    divergence_plot_matplotlib(filtered_df, post_code_select)

    score_column = st.selectbox(
        'Select the score column:',
        options=variables_list,
        index=0
    )
    
    # Call the function with the selected column
    plot_interactive(gdf_post_code, score_column)
    
