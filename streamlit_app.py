import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import json
from streamlit_autorefresh import st_autorefresh

API_KEY = "2c2142817f4478d07946764666ed4b77"
BASE_FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
BASE_WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

def get_weather_data(ville):
    params = {
        "q": ville,
        "appid": API_KEY,
        "units": "metric",
        "lang": "fr"
    }
    response = requests.get(BASE_WEATHER_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            "description": data["weather"][0]["description"].capitalize(),
            "icon": data["weather"][0]["icon"],
            "temperature": data["main"]["temp"],
            "humidite": data["main"]["humidity"],
            "vent": data["wind"]["speed"],
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"]
        }
    return None

def get_forecast_data(ville):
    params = {
        "q": ville,
        "appid": API_KEY,
        "units": "metric",
        "lang": "fr"
    }
    response = requests.get(BASE_FORECAST_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        forecast_list = data["list"]

        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        after_tomorrow = today + timedelta(days=2)

        previsions = {"Demain": [], "Après-demain": []}
        full_data = []

        for item in forecast_list:
            dt_txt = item["dt_txt"]
            dt_obj = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
            date = dt_obj.date()
            temp = item["main"]["temp"]
            desc = item["weather"][0]["description"]
            icon = item["weather"][0]["icon"]

            if date == tomorrow:
                previsions["Demain"].append((dt_txt, temp, desc, icon))
            elif date == after_tomorrow:
                previsions["Après-demain"].append((dt_txt, temp, desc, icon))

            full_data.append({
                "datetime": dt_txt,
                "temperature": temp
            })

        return previsions, full_data
    return None, None

def afficher_carte_meteo(lat, lon, meteo, ville):
    carte = folium.Map(location=[lat, lon], zoom_start=11)
    popup_text = f"{ville} : {meteo['description']}<br>🌡️ {meteo['temperature']}°C<br>💧 {meteo['humidite']}%<br>🌬️ {meteo['vent']} m/s"
    folium.Marker(
        location=[lat, lon],
        popup=popup_text,
        icon=folium.Icon(color="blue", icon="cloud")
    ).add_to(carte)
    st.subheader(f"🗺️ Carte météo - {ville}")
    st_folium(carte, width=700, height=500)

# ---------- Interface Streamlit ----------
st.set_page_config(page_title="Prévision Météo", page_icon="⛅", layout="centered")
st.title("🚜 Ferme Intelligente")

# 🎯 Saisie de la ville


# Sélectionner l'affichage via la barre latérale
option = st.sidebar.radio("Choisir l'affichage", ("Météo", "Données ESP32"))

if option == "Météo":
    st.subheader(("🌤️ Application de Prévision Météo"))
    ville = st.text_input("Entrez une ville", value="Monastir")
    if ville:
        meteo = get_weather_data(ville)
        previsions, full_data = get_forecast_data(ville)

        if meteo:
            st.subheader("📍 Météo Actuelle")
            col1, col2 = st.columns([1, 4])
            with col1:
                icon_url = f"http://openweathermap.org/img/wn/{meteo['icon']}@2x.png"
                st.image(icon_url)
            with col2:
                st.write(f"**Description :** {meteo['description']}")
                st.write(f"**Température :** {meteo['temperature']}°C")
                st.write(f"**Humidité :** {meteo['humidite']}%")
                st.write(f"**Vent :** {meteo['vent']} m/s")

            afficher_carte_meteo(meteo["lat"], meteo["lon"], meteo, ville)
        else:
            st.error("❌ Impossible de récupérer la météo actuelle.")

        if previsions:
            st.subheader("📅 Prévisions")
            for jour, liste in previsions.items():
                st.markdown(f"### {jour}")
                for dt, temp, desc, icon in liste:
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        icon_url = f"http://openweathermap.org/img/wn/{icon}.png"
                        st.image(icon_url, width=50)
                    with col2:
                        st.write(f"🕒 {dt} — 🌡️ {temp}°C — {desc.capitalize()}")
        else:
            st.error("❌ Impossible de récupérer les prévisions.")

        if full_data:
            st.subheader("📈 Évolution des Températures (5 jours)")
            df = pd.DataFrame(full_data)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)

            fig, ax = plt.subplots()
            df["temperature"].plot(ax=ax, marker="o", color="orange")
            ax.set_ylabel("Température (°C)")
            ax.set_xlabel("Date / Heure")
            ax.set_title(f"Prévision Température à {ville}")
            plt.xticks(rotation=45)
            st.pyplot(fig)

elif option == "Données ESP32":
    st.subheader("📡 Données reçues des ESP32")

    st_autorefresh(interval=2000, key="esp_data_refresh")

    try:
        with open("esp_data.json", "r") as f:
            data_esp = json.load(f)

        for item in reversed(data_esp[-10:]):  # Show the 10 most recent entries
            st.write(f"🕒 {item['timestamp']} | 🧿 {item['device']} - {item['sensor']} : **{item['value']}**")

    except FileNotFoundError:
        st.info("Aucune donnée reçue des ESP32 pour le moment.")
