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

# Mot de passe sécurisé
MOT_DE_PASSE_COACH = "RomainRB2004!"

# Initialisation des bases de données dans la session
if 'db_forme' not in st.session_state:
    st.session_state['db_forme'] = pd.DataFrame(columns=['Date', 'Sommeil', 'Fatigue', 'Stress', 'Humeur', 'Score_Forme', 'Douleur_Type', 'Zones_Douleur'])
    
if 'db_seances' not in st.session_state:
    st.session_state['db_seances'] = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge', 'Satisfaction'])

if 'db_soir' not in st.session_state:
    st.session_state['db_soir'] = pd.DataFrame(columns=['Date', 'Etat_Jour', 'Zones_Douleur_Soir', 'Type_Douleur'])

st.title("📊 Application de Suivi d'Entraînement & Santé")

tab_matin, tab_seance, tab_soir, tab_coach = st.tabs(["🌞 Check-in Matin", "🏋️ Bilan Séance", "🌙 Bilan Soir", "🔒 Vue Coach"])

# Liste anatomique complète enrichie (avec Psoas)
ZONES_ANATOMIQUES = [
    "Tête / Mâchoire",
    "Cervicales / Cou",
    "Trapèzes",
    "Épaules",
    "Biceps",
    "Triceps",
    "Coudes",
    "Avant-bras / Poignets / Mains",
    "Pectoraux",
    "Dorsaux / Grand dorsal",
    "Lombaires / Bas du dos",
    "Abdominaux / Obliques",
    "Psoas / Ilio-psoas",
    "Hanches / Adducteurs",
    "Fessiers",
    "Quadriceps",
    "Ischio-jambiers",
    "Genoux / Rotule",
    "Mollets (Gros Jumeaux / Soléaire)",
    "Tendons d'Achille",
    "Chevilles / Pieds"
]

# --- ONGLET 1 : MATIN ---
with tab_matin:
    st.header("Check-in Matinal")
    st.write("Évaluez votre état au réveil (1 = Très mauvais/bas, 5 = Excellent/haut).")
    
    date_matin = st.date_input("Date du jour", value=date.today(), key="date_m")
    
    col1, col2 = st.columns(2)
    with col1:
        sommeil = st.slider("Qualité du sommeil (1=Insomniaque, 5=Parfait)", 1, 5, 3)
        fatigue = st.slider("Niveau de fraîcheur / Fatigue (1=Épuisé, 5=Frais)", 1, 5, 3)
    with col2:
        stress = st.slider("Niveau de stress (1=Très stressé, 5=Zen)", 1, 5, 3)
        humeur = st.slider("Humeur (1=Mauvaise, 5=Excellente)", 1, 5, 3)
        
    st.markdown("---")
    st.subheader("Point Santé / Douleurs éventuelles")
    
    zones_matin = st.multiselect("Localisation(s) de la douleur ou gêne (plusieurs choix possibles) :", 
                                 ZONES_ANATOMIQUES, key="zones_m")
    
    type_douleur = st.selectbox("Si douleur, de quel type s'agit-il ?", [
        "Aucune",
        "Musculaire (douleur vive, type déchirure ou élongation)",
        "Articulaire (sensation de blocage ou d'instabilité, entorse)",
        "Tendineuse (apparaît progressivement à l'effort ou au réveil)",
        "Osseuse (très localisée et profonde)",
        "Ligamentaire (suite à une torsion)",
        "Neurologique (fourmillements, décharges)",
        "Courbatures (diffuses)",
        "Maladie (grippe, gastro...)",
        "Crampes"
    ], key="type_m")
    
    if st.button("Valider le Check-in Matin"):
        score_forme = sommeil + fatigue + stress + humeur
        zones_str = ", ".join(zones_matin) if zones_matin else "Aucune"
        
        nouvelle_forme = pd.DataFrame({
            'Date': [date_matin], 'Sommeil': [sommeil], 'Fatigue': [fatigue], 
            'Stress': [stress], 'Humeur': [humeur], 'Score_Forme': [score_forme],
            'Douleur_Type': [type_douleur], 'Zones_Douleur': [zones_str]
        })
        st.session_state['db_forme'] = pd.concat([st.session_state['db_forme'], nouvelle_forme], ignore_index=True)
        st.success(f"Check-in enregistré ! Score global de forme : {score_forme}/20")

# --- ONGLET 2 : SÉANCES ---
with tab_seance:
    st.header("Bilan de la Séance (sRPE)")
    st.write("À remplir dans les 30 minutes suivant l'effort.")
    
    date_seance = st.date_input("Date de la séance", value=date.today(), key="date_s")
    
    col3, col4 = st.columns(2)
    with col3:
        type_seance = st.selectbox("Type de séance", ["Prépa Physique", "Tennis - Entraînement", "Tennis - Match", "Récupération"])
        duree = st.number_input("Durée de la séance (minutes)", min_value=0, value=90)
    with col4:
        rpe = st.slider("Difficulté ressentie (RPE 1-10)", 1, 10, 5)
        satisfaction = st.slider("Satisfaction technique / tactique (1-5)", 1, 5, 3)
    
    if st.button("Enregistrer la séance"):
        charge = duree * rpe
        nouvelle_seance = pd.DataFrame({
            'Date': [date_seance], 'Type': [type_seance], 'Duree': [duree], 
            'RPE': [rpe], 'Charge': [charge], 'Satisfaction': [satisfaction]
        })
        st.session_state['db_seances'] = pd.concat([st.session_state['db_seances'], nouvelle_seance], ignore_index=True)
        st.success(f"Séance enregistrée ! Charge totale : {charge} unités.")

# --- ONGLET 3 : BILAN SOIR ---
with tab_soir:
    st.header("Flash Santé du Soir")
    st.write("Bilan de fin de journée sur l'impact de l'entraînement.")
    
    date_soir = st.date_input("Date du jour", value=date.today(), key="date_soir_k")
    
    etat_jour = st.radio("État du jour :", [
        "1 - Participation complète sans inconfort",
        "2 - Participation complète avec inconfort",
        "3 - Participation réduite à cause de la blessure",
        "4 - Absence complète à cause d'une blessure"
    ])
    
    zones_soir = st.multiselect("Localisation(s) de l'inconfort apparu ou persistant ce soir :", 
                                 ZONES_ANATOMIQUES, key="zones_s")
    
    type_soir = st.selectbox("Nature principale du ressenti du soir :", [
        "RAS / Normal",
        "Musculaire",
        "Articulaire",
        "Tendineuse",
        "Osseuse / Ligamentaire",
        "Autre (fatigue générale / maladie)"
    ], key="type_s")
    
    if st.button("Envoyer le bilan du soir"):
        zones_soir_str = ", ".join(zones_soir) if zones_soir else "Aucune"
        nouveau_soir = pd.DataFrame({
            'Date': [date_soir], 'Etat_Jour': [etat_jour], 
            'Zones_Douleur_Soir': [zones_soir_str], 'Type_Douleur': [type_soir]
        })
        st.session_state['db_soir'] = pd.concat([st.session_state['db_soir'], nouveau_soir], ignore_index=True)
        st.success("Bilan du soir enregistré avec succès !")

# --- ONGLET 4 : COACH ---
with tab_coach:
    st.header("Espace Staff / Coach")
    
    saisie_mdp = st.text_input("Entrez le mot de passe administrateur :", type="password")
    
    if saisie_mdp == MOT_DE_PASSE_COACH:
        st.success("Accès autorisé.")
        
        st.subheader("🌞 Suivi Forme Matinal (Hooper)")
        st.dataframe(st.session_state['db_forme'], use_container_width=True)
        
        st.subheader("🏋️ Historique des Séances & Charges (sRPE)")
        st.dataframe(st.session_state['db_seances'], use_container_width=True)
        
        st.subheader("🌙 Flash Santé du Soir")
        st.dataframe(st.session_state['db_soir'], use_container_width=True)
        
    elif saisie_mdp != "":
        st.error("Mot de passe incorrect.")
