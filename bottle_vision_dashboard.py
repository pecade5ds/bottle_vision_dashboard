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

st.write(df_docs.columns)

if tabs == "Main KPIs":
    st.header("Main KPIs")

    # danone_mkt_share = df_docs["total_danone"].sum() / df_docs["total_bottles"].sum()
    # non_danone_mkt_share = df_docs['total_non_danone'].sum() / df_docs["total_bottles"].sum()
    
    danone_shelf_share = (df_docs["total_danone"] / df_docs["total_bottles"]).mean()
    non_danone_shelf_share = (df_docs["total_non_danone"] / df_docs["total_bottles"]).mean()
    reminder_share = 1 - danone_shelf_share + non_danone_shelf_share
    
    # Divide el espacio en columnas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.plotly_chart(plot_gauge_from_scalar(danone_shelf_share.round(2), "Danone Shelf Share"), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_gauge_from_scalar(non_danone_shelf_share.round(2), "Competitor Shelf Share"), use_container_width=True)

    with col3:
        st.plotly_chart(plot_gauge_from_scalar(reminder_share, "Bottles Shelf Share"), use_container_width=True)

    correlations = {var: gdf_post_code ["Average Gross Income"].corr(gdf_post_code [var]) for var in variables_list}
    
    correlations_df = pd.DataFrame(list(correlations.items()), columns=["Variable", "Correlation"])
    
    correlations_fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(correlations_df["Variable"], correlations_df["Correlation"], color="skyblue")
    ax.set_xlabel("Correlation Gross Income by Brand")
    ax.set_title("Correlation Summary")
    ax.grid(axis="x", linestyle="--", alpha=0.7)
    st.pyplot(correlations_fig)

    
    # Tu código de Matplotlib
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    gdf_post_code.plot(
        column='total_danone',  # Variable para el gradiente
        cmap='Blues',  # Paleta de colores
        legend=True,  # Mostrar la leyenda
        legend_kwds={
            'label': "Danone Share",
            'orientation': "vertical"
        },
        ax=ax,
        edgecolor='black'  # Borde de los polígonos
    )
    
    ax.set_title("Danone Share Map", fontsize=14)
    ax.axis('off')  # Ocultar los ejes
    
    # Mostrar el gráfico en Streamlit
    st.pyplot(fig)


elif tabs == "Granular KPIs":
    st.header("Granular KPIs")
    

    
