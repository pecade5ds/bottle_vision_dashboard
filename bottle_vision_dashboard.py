import streamlit as st
import geopandas as gpd
import plotly.express as px

# Título del Dashboard
st.title("Dashboard de Ejemplo")

# Crear las pestañas
tabs = st.sidebar.radio("Selecciona una pestaña", ("Datos Generales", "Datos Geolocalizados"))

if tabs == "Datos Generales":
    st.header("Datos Generales")
    st.write("Aquí se muestran los datos generales.")
    # Puedes agregar tablas, gráficos u otros elementos aquí.
    
    # Ejemplo de un gráfico simple
    import pandas as pd
    df = pd.DataFrame({
        'Categoría': ['A', 'B', 'C', 'D'],
        'Valor': [10, 20, 30, 40]
    })
    st.write(df)
    st.bar_chart(df.set_index('Categoría'))

elif tabs == "Datos Geolocalizados":
    st.header("Datos Geolocalizados")
    st.write("Aquí se muestran los datos geolocalizados.")
    
    # Cargar un shapefile o datos geográficos
    # Ejemplo: cargar un shapefile de ejemplo
    # gdf = gpd.read_file("ruta/a/tu/archivo.shp")
    
    # Para este ejemplo, generamos algunos datos geográficos falsos
    gdf = gpd.GeoDataFrame({
        'id': [1, 2, 3],
        'nombre': ['Ubicación 1', 'Ubicación 2', 'Ubicación 3'],
        'geometry': [
            gpd.GeoSeries.from_wkt('POINT (0 0)').iloc[0],
            gpd.GeoSeries.from_wkt('POINT (1 1)').iloc[0],
            gpd.GeoSeries.from_wkt('POINT (2 2)').iloc[0],
        ]
    })
    
    # Mapa de los datos geolocalizados
    fig = px.scatter_geo(gdf, lat=gdf.geometry.y, lon=gdf.geometry.x, text=gdf['nombre'])
    st.plotly_chart(fig)
