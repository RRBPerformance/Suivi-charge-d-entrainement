#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 14:27:14 2026

@author: romainromeyerbouchard
"""

import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Suivi de Charge", layout="wide")

# Initialisation des deux bases de données distinctes
if 'db_forme' not in st.session_state:
    st.session_state['db_forme'] = pd.DataFrame(columns=['Date', 'Sommeil', 'Douleurs', 'Humeur', 'Score_Forme'])
    
if 'db_seances' not in st.session_state:
    st.session_state['db_seances'] = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge'])

st.title("📊 Application de Suivi d'Entraînement")

# Création des trois onglets
tab_matin, tab_seance, tab_coach = st.tabs(["🌞 Check-in Matin", "🏋️ Bilan Séance", "📈 Vue Coach"])

# --- ONGLET 1 : MATIN ---
with tab_matin:
    st.header("Check-in Matinal")
    st.write("À remplir une seule fois, au réveil.")
    
    date_matin = st.date_input("Date", value=date.today(), key="date_m")
    sommeil = st.slider("Qualité du sommeil (1-5)", 1, 5, 3)
    douleurs = st.slider("Douleurs / Courbatures (1=Fortes, 5=Aucune)", 1, 5, 3)
    humeur = st.slider("Humeur / Stress (1=Mauvaise, 5=Excellente)", 1, 5, 3)
    
    if st.button("Envoyer le check-in matin"):
        score = sommeil + douleurs + humeur # Calcul simple du score global
        nouvelle_forme = pd.DataFrame({
            'Date': [date_matin], 'Sommeil': [sommeil], 'Douleurs': [douleurs], 'Humeur': [humeur], 'Score_Forme': [score]
        })
        st.session_state['db_forme'] = pd.concat([st.session_state['db_forme'], nouvelle_forme], ignore_index=True)
        st.success("État de forme enregistré !")

# --- ONGLET 2 : SÉANCES ---
with tab_seance:
    st.header("Bilan de la Séance")
    st.write("À remplir dans les 30 minutes après chaque entraînement.")
    
    date_seance = st.date_input("Date", value=date.today(), key="date_s")
    type_seance = st.selectbox("Type de séance", ["Prépa Physique", "Tennis", "Récupération", "Match"])
    duree = st.number_input("Durée (minutes)", min_value=0, value=90)
    rpe = st.slider("Difficulté RPE (1-10)", 1, 10, 5)
    
    if st.button("Enregistrer la séance"):
        charge = duree * rpe
        nouvelle_seance = pd.DataFrame({
            'Date': [date_seance], 'Type': [type_seance], 'Duree': [duree], 'RPE': [rpe], 'Charge': [charge]
        })
        st.session_state['db_seances'] = pd.concat([st.session_state['db_seances'], nouvelle_seance], ignore_index=True)
        st.success("Séance ajoutée avec succès !")

# --- ONGLET 3 : COACH ---
with tab_coach:
    st.header("Tableau de Bord")
    
    st.subheader("Données de Forme (Matin)")
    st.dataframe(st.session_state['db_forme'], use_container_width=True)
    
    st.subheader("Historique des Séances")
    st.dataframe(st.session_state['db_seances'], use_container_width=True)