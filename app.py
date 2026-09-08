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

# Mot de passe pour la vue coach
MOT_DE_PASSE_COACH = "Coach365"

# Initialisation des deux bases de données distinctes
if 'db_forme' not in st.session_state:
    st.session_state['db_forme'] = pd.DataFrame(columns=['Date', 'Sommeil', 'Douleurs', 'Zone_Douleur', 'Humeur', 'Nutrition', 'Score_Forme'])
    
if 'db_seances' not in st.session_state:
    st.session_state['db_seances'] = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge', 'Satisfaction'])

st.title("📊 Application de Suivi d'Entraînement")

tab_matin, tab_seance, tab_coach = st.tabs(["🌞 Check-in Matin", "🏋️ Bilan Séance", "🔒 Vue Coach"])

# --- ONGLET 1 : MATIN ---
with tab_matin:
    st.header("Check-in Matinal")
    st.write("À remplir une seule fois, au réveil.")
    
    date_matin = st.date_input("Date", value=date.today(), key="date_m")
    
    col1, col2 = st.columns(2)
    with col1:
        sommeil = st.slider("Qualité du sommeil (1-5)", 1, 5, 3)
        humeur = st.slider("Humeur / Niveau de stress (1-5)", 1, 5, 3)
        nutrition = st.slider("Qualité hydratation/repas de la veille (1-5)", 1, 5, 3)
        
    with col2:
        douleurs = st.slider("Niveau de courbatures/douleurs (1=Fortes, 5=Aucune)", 1, 5, 3)
        zones = st.multiselect("Si douleur(s), sur quelle(s) zone(s) ?", 
                               ["Aucune", "Épaule / Coude", "Poignet", "Dos", "Hanches / Pubis", "Genoux", "Mollets / Chevilles"])
    
    if st.button("Envoyer le check-in matin"):
        score = sommeil + douleurs + humeur + nutrition
        zones_str = ", ".join(zones) if zones else "Non spécifié"
        
        nouvelle_forme = pd.DataFrame({
            'Date': [date_matin], 'Sommeil': [sommeil], 'Douleurs': [douleurs], 
            'Zone_Douleur': [zones_str], 'Humeur': [humeur], 'Nutrition': [nutrition], 'Score_Forme': [score]
        })
        st.session_state['db_forme'] = pd.concat([st.session_state['db_forme'], nouvelle_forme], ignore_index=True)
        st.success("État de forme enregistré avec succès !")

# --- ONGLET 2 : SÉANCES ---
with tab_seance:
    st.header("Bilan de la Séance")
    st.write("À remplir dans les 30 minutes après chaque entraînement ou match.")
    
    date_seance = st.date_input("Date de la séance", value=date.today(), key="date_s")
    
    col3, col4 = st.columns(2)
    with col3:
        type_seance = st.selectbox("Type de séance", ["Prépa Physique", "Tennis - Entraînement", "Tennis - Match", "Récupération"])
        duree = st.number_input("Durée (minutes)", min_value=0, value=90)
    with col4:
        rpe = st.slider("Difficulté ressentie (RPE 1-10)", 1, 10, 5)
        satisfaction = st.slider("Satisfaction globale de votre performance (1-5)", 1, 5, 3)
    
    if st.button("Enregistrer la séance"):
        charge = duree * rpe
        nouvelle_seance = pd.DataFrame({
            'Date': [date_seance], 'Type': [type_seance], 'Duree': [duree], 
            'RPE': [rpe], 'Charge': [charge], 'Satisfaction': [satisfaction]
        })
        st.session_state['db_seances'] = pd.concat([st.session_state['db_seances'], nouvelle_seance], ignore_index=True)
        st.success("Séance ajoutée à la base de données !")

# --- ONGLET 3 : COACH ---
with tab_coach:
    st.header("Espace Réservé au Staff")
    
    # Système de sécurité basique
    saisie_mdp = st.text_input("Veuillez entrer le mot de passe pour accéder aux données :", type="password")
    
    if saisie_mdp == MOT_DE_PASSE_COACH:
        st.success("Accès autorisé.")
        
        st.subheader("Données de Forme (Matin)")
        st.dataframe(st.session_state['db_forme'], use_container_width=True)
        
        st.subheader("Historique des Séances et Charges")
        st.dataframe(st.session_state['db_seances'], use_container_width=True)
    elif saisie_mdp != "":
        st.error("Mot de passe incorrect.")
