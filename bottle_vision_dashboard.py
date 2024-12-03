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
    left_on=["COD_POSTAL"],
    right_on=["ZIP_code"],
    how="inner"
)

# merge post codes and detections
post_code_data  = df_docs[df_docs.columns.intersection(list(competitor_danone_labels_dict.keys()) + ["post_code",'total_danone', 'total_non_danone', 'total_bottles'])].groupby("post_code").sum().reset_index()
gdf_post_code = gdf_post_code.merge(post_code_data, left_on="COD_POSTAL", right_on="post_code",how="left").drop(["ID_CP","post_code","ALTA_DB","ZIP_code","CODIGO_INE"] ,axis=1)

tabs = st.radio("Selecciona una pestaña", ("Datos Generales", "Datos Geolocalizados"))

if tabs == "Datos Generales":
    st.header("Datos Generales")
    st.write("Aquí se muestran los datos generales.")


elif tabs == "Datos Geolocalizados":
    st.header("Datos Geolocalizados")
    st.write("Aquí se muestran los datos geolocalizados.")
    
