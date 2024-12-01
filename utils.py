import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import plotly.express as px
import plotly.graph_objects as go

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

    df_docs["danone_share"] = df_docs["total_danone"]/df_docs["total_bottles"]

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

    return fig

def divergence_plot_matplotlib(df, codigo_postal):
    df_filtered = df[df['post_code'] == codigo_postal]

    danone = df_filtered[df_filtered['Category'] == 'Danone']
    competidor = df_filtered[df_filtered['Category'] == 'competitor']

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(danone['brand'], danone['value'], color='blue', label='Danone')
    ax.barh(competidor['brand'], competidor['value'], color='red', label='Competitor')

    ax.set_title(f"Brand by Post Code: {codigo_postal} (Competitor vs Danone)", fontsize=14)
    ax.set_xlabel("Value", fontsize=12)
    ax.set_ylabel("Brand", fontsize=12)
    ax.axvline(0, color='black', linewidth=0.8, linestyle='--')  # Línea vertical en 0
    ax.legend(loc='upper right', fontsize=12)

    # Mostrar el gráfico
    plt.tight_layout()
    plt.show()

def plot_interactive(gdf_data_input, score_column):

    cmap = LinearSegmentedColormap.from_list("custom_cmap", ["blue", "white", "red"])

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    gdf_data_input.plot(column=score_column, cmap=cmap, legend=True, ax=ax, edgecolor="black")
    ax.set_title(f"CP by '{score_column}'", fontsize=16)
    ax.axis("off")
    plt.show()
