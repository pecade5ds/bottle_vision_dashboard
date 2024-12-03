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

# App Title
st.title("Bottle Vision Dashboard")

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
variables_list = df_docs.columns.intersection(brand_list)

post_code_data  = df_docs.drop(["store_type","store_name","shelf id"],axis=1).groupby("COD_POSTAL").sum().reset_index()

gdf_post_code = gdf_post_code.merge(post_code_data, 
                                    on="COD_POSTAL", 
                                    how="left")

tabs = st.radio("Selecciona una pestaña", ("Main KPIs", "Granular KPIs"))

if tabs == "Main KPIs":
    st.header("Main KPIs")

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
    
    col2_1, col2_2, col2_3 = st.columns(3)
    
    with col2_1:
        correlations_fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(correlations_df["Variable"], correlations_df["Correlation"], color="skyblue")
        ax.set_xlabel("Correlation Gross Income by Brand")
        ax.set_title("Correlation Summary")
        ax.grid(axis="x", linestyle="--", alpha=0.7)
        st.pyplot(correlations_fig)
        
    with col2_2:
        fig_map_danone, ax = plt.subplots(1, 1, figsize=(10, 6))
        gdf_post_code.plot(
            column='total_danone',
            cmap='Blues', 
            legend=True,  
            legend_kwds={
                'label': "Danone Share",
                'orientation': "vertical"
            },
            ax=ax,
            edgecolor='black'
        )
        
        ax.set_title("Danone Share Map", fontsize=14)
        ax.axis('off') 
        
        st.pyplot(fig_map_danone)
    with col2_3:
        podium_df = pd.DataFrame({
        "Product": df_docs[variables_list].sum().index,
        "Share": (df_docs[variables_list].sum().values / df_docs["total_bottles"].sum() * 100).round(1),
        "Category": [competitor_danone_labels_dict[col] for col in variables_list]})
    
        fig_comp_danone = px.bar(
            podium_df,
            x="Product",
            y="Share",
            color="Category",
            color_discrete_map={
                "Danone": "blue",
                "competitor": "red"
            },
            title="Top and Bottom Products (Danone vs Competitors)",
            text="Share"
        )
        
        fig_comp_danone.update_traces(textposition="outside")
        fig_comp_danone.update_layout(xaxis_title="Products", yaxis_title="Values", template="plotly_white")
        

elif tabs == "Granular KPIs":
    st.header("Granular KPIs")



st.plotly_chart(fig_comp_danone)

    
        
