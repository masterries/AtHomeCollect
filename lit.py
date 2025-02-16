import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
import json

# Datenbankverbindung herstellen
@st.cache_data
def load_data():
    conn = sqlite3.connect('athome_listings.db')
    query = """
    SELECT 
        id, type, price, 
        "address.city" as city,
        "address.pin.lat" as lat,
        "address.pin.lon" as lon,
        "characteristic.rooms" as rooms,
        "characteristic.surface" as surface,
        "characteristic.bedrooms" as bedrooms,
        status,
        transaction,
        format
    FROM listings
    WHERE price IS NOT NULL
    AND "address.pin.lat" IS NOT NULL
    AND "address.pin.lon" IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    st.title("Immobilien-Dashboard Luxembourg")
    
    # Daten laden
    df = load_data()
    
    # Sidebar Filter
    st.sidebar.header("Filter")
    
    # Preisbereich
    price_range = st.sidebar.slider(
        "Preisbereich (€)",
        float(df['price'].min()),
        float(df['price'].max()),
        (float(df['price'].min()), float(df['price'].max()))
    )
    
    # Immobilientyp
    property_types = st.sidebar.multiselect(
        "Immobilientyp",
        options=df['type'].unique(),
        default=df['type'].unique()
    )
    
    # Transaktionsart
    transactions = st.sidebar.multiselect(
        "Transaktionsart",
        options=df['transaction'].unique(),
        default=df['transaction'].unique()
    )
    
    # Daten filtern
    filtered_df = df[
        (df['price'].between(price_range[0], price_range[1])) &
        (df['type'].isin(property_types)) &
        (df['transaction'].isin(transactions))
    ]
    
    # Dashboard Layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Durchschnittspreis nach Immobilientyp")
        fig_avg_price = px.bar(
            filtered_df.groupby('type')['price'].mean().reset_index(),
            x='type',
            y='price',
            title="Durchschnittspreis nach Immobilientyp"
        )
        st.plotly_chart(fig_avg_price)
    
    with col2:
        st.subheader("Anzahl Immobilien nach Status")
        fig_status = px.pie(
            filtered_df,
            names='status',
            title="Verteilung nach Status"
        )
        st.plotly_chart(fig_status)
    
    # Karte
    st.subheader("Immobilien Standorte")
    m = folium.Map(
        location=[49.815273, 6.129583],  # Zentrum von Luxemburg
        zoom_start=10
    )
    
    for idx, row in filtered_df.iterrows():
        folium.Marker(
            [row['lat'], row['lon']],
            popup=f"Typ: {row['type']}<br>Preis: €{row['price']:,.2f}<br>Status: {row['status']}"
        ).add_to(m)
    
    folium_static(m)
    
    # Detaillierte Statistiken
    st.subheader("Detaillierte Statistiken")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        st.metric(
            "Durchschnittspreis",
            f"€{filtered_df['price'].mean():,.2f}"
        )
    
    with col4:
        st.metric(
            "Anzahl Immobilien",
            len(filtered_df)
        )
    
    with col5:
        st.metric(
            "Durchschnittliche Wohnfläche",
            f"{filtered_df['surface'].mean():,.2f} m²"
        )
    
    # Datentabelle
    st.subheader("Immobilien Liste")
    st.dataframe(
        filtered_df[['type', 'price', 'city', 'rooms', 'surface', 'status', 'transaction']]
    )

if __name__ == "__main__":
    st.set_page_config(
        page_title="Immobilien Dashboard",
        page_icon="🏠",
        layout="wide"
    )
    main()
