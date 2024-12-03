import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def preprocess_docs(docs, competitor_danone_labels_dict):
    # Normalize the JSON data and flatten it into a DataFrame
    df_docs = pd.json_normalize([elem.to_dict() for elem in docs], sep='_')

    # Fill missing values with 0
    df_docs.fillna(0, inplace=True)

    # Remove records where photo_type is 'Test'
    df_docs.query("photo_type == 'Prod'", inplace=True)

    # Clean up column names, removing the 'predictions_' prefix
    df_docs.columns = [col.replace('predictions_', '') if 'predictions_' in col else col for col in df_docs.columns]

    # Calculate total for Danone products based on the provided label mapping
    df_docs['total_danone'] = df_docs[[col for col in df_docs.columns if competitor_danone_labels_dict.get(col, '') == 'Danone']].sum(axis=1)

    # Calculate total for non Danone products based on the provided label mapping
    df_docs['total_non_danone'] = df_docs[[col for col in df_docs.columns if competitor_danone_labels_dict.get(col, '') == 'competitor']].sum(axis=1)


    # Calculate the predicted total by summing competitor and Danone totals
    df_docs["predicted_total"] = df_docs['total_non_danone'] + df_docs['total_danone']

    # Ensure that the total bottles are at least as large as the predicted total
    df_docs['total_bottles'] = np.maximum(df_docs['predicted_total'], df_docs['Num_bottles'])

    df_docs["danone_share"] = round(df_docs["total_danone"]/df_docs["total_bottles"],2) *100

    # Drop unnecessary columns
    df_docs.drop(["predicted_total", "Num_bottles"], axis=1, inplace=True)

    # Group by relevant columns and aggregate the data (sum) based on these columns
    df_docs = df_docs.groupby(['post_code', 'store_type', 'store_name', 'shelf id']).sum().reset_index().drop(["photo_type"], axis=1)

    return df_docs

def plot_gauge_from_scalar(score, score_column):
    colname = score_column  # Usamos el nombre de la columna como título

    # Determinar el color del medidor
    if score < 0.5:
        gauge_color = "red"
    elif 0.5 <= score < 0.75:
        gauge_color = "yellow"
    else:
        gauge_color = "green"

    # Crear la figura del medidor
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': colname},  # Usamos el nombre de la columna como título
        gauge={
            'axis': {'range': [0, 1], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': gauge_color},
            'steps': [
                {'range': [0, 0.5], 'color': "lightgray"},
                {'range': [0.5, 1], 'color': "lightgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        margin={'t': 0, 'b': 0, 'l': 0, 'r': 0},  # Remove margins
        height=250  # Adjust the height to your desired size
    )

    return fig

def divergence_plot_matplotlib(df, codigo_postal):
    df_filtered = df[df['COD_POSTAL'] == codigo_postal]

    danone = df_filtered[df_filtered['Category'] == 'Danone']
    competidor = df_filtered[df_filtered['Category'] == 'competitor']

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(danone['brand'], danone['value'], color='blue', label='Danone')
    ax.barh(competidor['brand'], competidor['value'], color='red', label='Competitor')

    # Ajuste del título y los ejes
    ax.set_title(f"Brand by Post Code: {codigo_postal} (Competitor vs Danone)", fontsize=14)
    ax.set_xlabel("Value", fontsize=12)
    ax.set_ylabel("Brand", fontsize=12)
    ax.axvline(0, color='black', linewidth=0.8, linestyle='--')  # Línea vertical en 0

    # Configuración de los valores del eje x para mostrar solo valores positivos
    ax.set_xticks(ax.get_xticks())  # Obtener los valores del eje X
    ax.set_xticklabels([abs(x) for x in ax.get_xticks()])  # Mostrar solo valores positivos

    ax.legend(loc='upper right', fontsize=12)

    # Mostrar el gráfico en Streamlit
    plt.tight_layout()
    st.pyplot(fig)  # Aquí usamos st.pyplot para mostrar el gráfico

def plot_interactive(gdf_data_input, score_column):
    # Create the map with Plotly Express
    fig = px.choropleth(gdf_data_input, 
                        geojson=gdf_data_input.geometry, # GeoJSON column (adjust according to your data)
                        locations=gdf_data_input.index, # Index of your dataframe, adjust if needed
                        color=score_column, 
                        hover_name="COD_POSTAL",  # Adjust this to a column you want to show in hover info
                        hover_data={
                        'COD_POSTAL': True,  # Display the 'COD_POSTAL' column
                        'Average Gross Income': True,  # Add more columns as needed
                        'danone_share': True},
                        color_continuous_scale=["white","darkblue"], 
                        title=f"Post code presence: '{score_column}'")

    # Update the map layout
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(title_text=f"Postcode presence: '{score_column}'", title_x=0.5)

    # Show the plot
    st.plotly_chart(fig)

def plot_correlation(correlations_df):
    # Crear la figura usando Plotly
    fig = go.Figure(go.Bar(
        x=correlations_df["Correlation"], 
        y=correlations_df["Variable"], 
        orientation='h',  # Gráfico de barras horizontales
        marker=dict(color='skyblue')  # Color de las barras
    ))

    # Agregar título y etiquetas
    fig.update_layout(
        title="Correlation Summary",
        xaxis_title="Correlation Gross Income by Brand",
        yaxis_title="Brands",
        template="plotly_white",  # Estilo visual limpio
        xaxis=dict(showgrid=True, gridcolor='lightgray'),
        yaxis=dict(showgrid=False)
    )
    
    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
def plot_danone_share_map(gdf_post_code):
    # Create the choropleth map
    fig_map_danone = px.choropleth(
        gdf_post_code,
        geojson=gdf_post_code.geometry,
        locations=gdf_post_code.index,  # or a column with unique identifiers
        color='total_danone',
        color_continuous_scale='Blues',
        labels={'total_danone': 'Danone Share'},
        hover_data={'total_danone': True, 
                    'COD_POSTAL': True,
                    'Average Gross Income': True,
                    'danone_share': True},  
    )
    
    # Update layout to remove axis and add a title
    fig_map_danone.update_geos(fitbounds="locations")
    fig_map_danone.update_layout(
        title="Danone Share Map",
        geo=dict(showcoastlines=True, coastlinecolor="Black", showland=True, landcolor="white"),
    )

    # Display the map in Streamlit
    st.plotly_chart(fig_map_danone)

def plot_competitor_share(podium_df):
    # Crear el gráfico de barras
    fig = px.bar(
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
    
    # Ajustar la posición del texto y el diseño
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="Products", 
        yaxis_title="Values", 
        template="plotly_white"
    )
    
    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)
