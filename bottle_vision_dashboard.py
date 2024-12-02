import pandas as pd
import numpy as np
import streamlit as st
import geopandas as gpd
import plotly.express as px
from utils import *
import json

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests

# Título de la app
st.title("Bottle Vision Dashboard")

# Firebase credentials (solo se carga una vez)
@st.cache_resource
def load_firebase_credentials():
    return firestore.Client.from_service_account_info(st.secrets["firebase"])

db = load_firebase_credentials()

# Configuración (se carga solo una vez)
@st.cache_data
def load_config():
    with open('./Data/config/query_config.json', 'r') as json_file:
        return json.load(json_file)

config_data = load_config()
db_schema_name_str = config_data["db_schema_name"]

# Cargar las etiquetas de competidores (se carga solo una vez)
@st.cache_data
def load_competitor_labels():
    with open('./Data/competitor_danone_labels_dict.json', 'r') as json_file:
        return json.load(json_file)

competitor_danone_labels_dict = load_competitor_labels()

# Conexión con Firebase (se carga solo una vez)
@st.cache_data
def fetch_firebase_data():
    docs = db.collection(db_schema_name_str).get()
    return docs

docs = fetch_firebase_data()

# Preprocesamiento de los documentos de Firebase
@st.cache_data
def preprocess_firebase_docs(docs, competitor_danone_labels_dict):
    return preprocess_docs(docs, competitor_danone_labels_dict)

df_docs = preprocess_firebase_docs(docs, competitor_danone_labels_dict)

# Cargar el salario bruto de los códigos postales (solo una vez)
@st.cache_data
def load_gross_salary_data():
    gross_salary_postcode_df = pd.read_csv("./Data/renta_barcelona.csv", sep=";", decimal=",")
    gross_salary_postcode_df['Cat_avg_Gross_Income'] = pd.qcut(gross_salary_postcode_df['Average Gross Income'], q=3, labels=['Low', 'Medium', 'High'])
    gross_salary_postcode_df['Cat_avg_Disposable_Income'] = pd.qcut(gross_salary_postcode_df['Average Disposable Income'], q=3, labels=['Low', 'Medium', 'High'])
    return gross_salary_postcode_df

gross_salary_postcode_df = load_gross_salary_data()

# Cargar el GeoJSON de códigos postales de Barcelona (se carga solo una vez)
@st.cache_data
def load_postcode_geojson():
    return gpd.read_file('./Data/BARCELONA.geojson')

gdf_post_code = load_postcode_geojson()

# Realizar las fusiones de manera eficiente
@st.cache_data
def preprocess_postcode_data(gdf_post_code, gross_salary_postcode_df, df_docs, competitor_danone_labels_dict):
    gdf_post_code = gdf_post_code.merge(
        gross_salary_postcode_df,
        left_on=["COD_POSTAL"],
        right_on=["ZIP_code"],
        how="inner"
    )

    post_code_data  = df_docs[df_docs.columns.intersection(list(competitor_danone_labels_dict.keys()) + ["post_code",'total_danone', 'total_non_danone', 'total_bottles'])].groupby("post_code").sum().reset_index()
    gdf_post_code = gdf_post_code.merge(post_code_data, left_on="COD_POSTAL", right_on="post_code", how="left").drop(["ID_CP","post_code","ALTA_DB","ZIP_code","CODIGO_INE"], axis=1)
    return gdf_post_code

gdf_post_code = preprocess_postcode_data(gdf_post_code, gross_salary_postcode_df, df_docs, competitor_danone_labels_dict)

# Mostrar resultados o visualizaciones aquí
# ...

# tabs = st.radio("Selecciona una pestaña", ("Datos Generales", "Datos Geolocalizados"))

# if tabs == "Datos Generales":
#     st.header("Datos Generales")
#     st.write("Aquí se muestran los datos generales.")


# elif tabs == "Datos Geolocalizados":
#     st.header("Datos Geolocalizados")
#     st.write("Aquí se muestran los datos geolocalizados.")
    
