#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 14:27:14 2026

@author: romainromeyerbouchard
"""

import streamlit as st
import pandas as pd
from datetime import date

# Configuration de la page
st.set_page_config(page_title="Suivi de Charge RRB", page_icon="🎾", layout="wide")

# Mot de passe sécurisé
MOT_DE_PASSE_COACH = "RomainRB2004!"

# Initialisation des bases de données dans la session
if 'db_forme' not in st.session_state:
    st.session_state['db_forme'] = pd.DataFrame(columns=['Date', 'Sommeil', 'Fatigue', 'Stress', 'Humeur', 'Score_Forme', 'Douleur_Type', 'Zones_Douleur'])
    
if 'db_seances' not in st.session_state:
    st.session_state['db_seances'] = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge', 'Satisfaction'])

if 'db_soir' not in st.session_state:
    st.session_state['db_soir'] = pd.DataFrame(columns=['Date', 'Etat_Jour', 'Zones_Douleur_Soir', 'Type_Douleur'])

# Titre principal
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Académie Tennis : Suivi de la Performance</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280;'>Monitoring quotidien - Optimisation et Prévention</p>", unsafe_allow_html=True)
st.divider()

tab_matin, tab_seance, tab_soir, tab_coach = st.tabs(["🌅 Check-in Matin", "👟 Bilan Séance", "🌙 Flash Soir", "🔐 Espace Coach"])

# Liste anatomique complète enrichie (avec Psoas)
ZONES_ANATOMIQUES = [
    "Tête / Mâchoire", "Cervicales / Cou", "Trapèzes", "Épaules", "Biceps", "Triceps", "Coudes", 
    "Avant-bras / Poignets / Mains", "Pectoraux", "Dorsaux / Grand dorsal", "Lombaires / Bas du dos", 
    "Abdominaux / Obliques", "Psoas / Ilio-psoas", "Hanches / Adducteurs", "Fessiers", "Quadriceps", 
    "Ischio-jambiers", "Genoux / Rotule", "Mollets (Gros Jumeaux / Soléaire)", "Tendons d'Achille", "Chevilles / Pieds"
]

# --- ONGLET 1 : MATIN ---
with tab_matin:
    st.info("💡 **Consigne :** À remplir chaque matin au réveil pour adapter la charge de la journée.")
    date_matin = st.date_input("📅 Date du jour", value=date.today(), key="date_m")
    
    st.markdown("### 🧠 État de Forme (Hooper)")
    col1, col2 = st.columns(2)
    with col1:
        sommeil = st.slider("💤 Qualité du sommeil (1=Insomniaque, 5=Parfait)", 1, 5, 3)
        fatigue = st.slider("🔋 Niveau de fraîcheur (1=Épuisé, 5=Frais)", 1, 5, 3)
    with col2:
        stress = st.slider("🌪️ Niveau de stress (1=Très stressé, 5=Zen)", 1, 5, 3)
        humeur = st.slider("😊 Humeur (1=Mauvaise, 5=Excellente)", 1, 5, 3)
        
    st.markdown("### 🩺 Point Clinique Matinal")
    zones_matin = st.multiselect("📍 Localisation(s) de la douleur ou gêne :", ZONES_ANATOMIQUES, key="zones_m")
    type_douleur = st.selectbox("⚡ Quel est le type de douleur ?", [
        "Aucune", "Musculaire (déchirure, élongation)", "Articulaire (blocage, instabilité)", 
        "Tendineuse (progressive à l'effort)", "Osseuse (profonde)", "Ligamentaire (torsion)", 
        "Neurologique (fourmillements)", "Courbatures (diffuses)", "Maladie (grippe, gastro...)", "Crampes"
    ], key="type_m")
    
    if st.button("✅ Valider le Check-in Matin", use_container_width=True):
        score_forme = sommeil + fatigue + stress + humeur
        zones_str = ", ".join(zones_matin) if zones_matin else "Aucune"
        nouvelle_forme = pd.DataFrame({
            'Date': [date_matin], 'Sommeil': [sommeil], 'Fatigue': [fatigue], 
            'Stress': [stress], 'Humeur': [humeur], 'Score_Forme': [score_forme],
            'Douleur_Type': [type_douleur], 'Zones_Douleur': [zones_str]
        })
        st.session_state['db_forme'] = pd.concat([st.session_state['db_forme'], nouvelle_forme], ignore_index=True)
        st.success(f"🎉 Parfait ! Ton score de forme aujourd'hui est de {score_forme}/20. Bon entraînement !")

# --- ONGLET 2 : SÉANCES ---
with tab_seance:
    st.warning("⏱️ **Rappel :** À remplir dans les 30 minutes suivant la fin de l'effort pour une donnée sRPE fiable.")
    date_seance = st.date_input("📅 Date de la séance", value=date.today(), key="date_s")
    
    col3, col4 = st.columns(2)
    with col3:
        type_seance = st.selectbox("🎾 Type de séance", ["Prépa Physique", "Tennis - Entraînement", "Tennis - Match", "Récupération / Soins"])
        duree = st.number_input("⏱️ Durée de la séance (minutes)", min_value=0, value=90, step=15)
    with col4:
        rpe = st.slider("🥵 Difficulté ressentie (RPE 1-10)", 1, 10, 5)
        satisfaction = st.slider("🎯 Satisfaction technique / tactique (1-5)", 1, 5, 3)
    
    if st.button("🔥 Enregistrer la séance", use_container_width=True):
        charge = duree * rpe
        nouvelle_seance = pd.DataFrame({
            'Date': [date_seance], 'Type': [type_seance], 'Duree': [duree], 
            'RPE': [rpe], 'Charge': [charge], 'Satisfaction': [satisfaction]
        })
        st.session_state['db_seances'] = pd.concat([st.session_state['db_seances'], nouvelle_seance], ignore_index=True)
        st.success(f"📊 Séance validée ! Charge calculée : {charge} unités.")

# --- ONGLET 3 : BILAN SOIR ---
with tab_soir:
    st.info("🌙 **Flash Soir :** Dernier bilan avant la récupération nocturne.")
    date_soir = st.date_input("📅 Date du jour", value=date.today(), key="date_soir_k")
    etat_jour = st.radio("🚦 Bilan de la participation du jour :", [
        "🟢 1 - Participation complète sans inconfort",
        "🟡 2 - Participation complète avec inconfort",
        "🟠 3 - Participation réduite à cause de la blessure",
        "🔴 4 - Absence complète à cause d'une blessure"
    ])
    zones_soir = st.multiselect("📍 Localisation(s) de l'inconfort ce soir :", ZONES_ANATOMIQUES, key="zones_s")
    type_soir = st.selectbox("⚡ Nature principale du ressenti :", [
        "RAS / Normal", "Musculaire", "Articulaire", "Tendineuse", "Osseuse / Ligamentaire", "Autre"
    ], key="type_s")
    
    if st.button("💤 Envoyer le bilan du soir", use_container_width=True):
        zones_soir_str = ", ".join(zones_soir) if zones_soir else "Aucune"
        nouveau_soir = pd.DataFrame({
            'Date': [date_soir], 'Etat_Jour': [etat_jour], 
            'Zones_Douleur_Soir': [zones_soir_str], 'Type_Douleur': [type_soir]
        })
        st.session_state['db_soir'] = pd.concat([st.session_state['db_soir'], nouveau_soir], ignore_index=True)
        st.success("✅ Bilan du soir enregistré. Bonne récupération !")

# --- ONGLET 4 : COACH AVEC GRAPHIQUES AVANCÉS ---
with tab_coach:
    st.markdown("### 🔐 Espace Réservé au Staff")
    saisie_mdp = st.text_input("Entrez le mot de passe administrateur :", type="password")
    
    if saisie_mdp == MOT_DE_PASSE_COACH:
        st.success("🔓 Accès autorisé.")
        
        st.markdown("---")
        st.markdown("## 📈 Tableaux de Bord & Tendances de Charge")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📉 Évolution du Score de Forme (Matin)")
            if not st.session_state['db_forme'].empty:
                df_forme_chart = st.session_state['db_forme'].set_index('Date')[['Score_Forme']]
                st.line_chart(df_forme_chart)
            else:
                st.info("Pas assez de données pour afficher le graphique de forme.")
                
        with col_g2:
            st.subheader("📊 Charges d'Entraînement & Fenêtres Glissantes")
            if not st.session_state['db_seances'].empty:
                # Choix de la vue pour les charges
                vue_charge = st.radio("Mode d'affichage des charges :", ["Séances par type (Empilé)", "Moyenne glissante (7j / 5j / 3j)"], horizontal=True)
                
                df_s = st.session_state['db_seances'].copy()
                df_s['Date'] = pd.to_datetime(df_s['Date'])
                
                if vue_charge == "Séances par type (Empilé)":
                    # Tableau pivot pour avoir les types de séances en colonnes (empilement automatique par Streamlit)
                    df_pivot = df_s.pivot_table(index='Date', columns='Type', values='Charge', aggfunc='sum').fillna(0)
                    st.bar_chart(df_pivot)
                else:
                    # Calcul des moyennes glissantes sur la charge totale par jour
                    df_jour = df_s.groupby('Date')['Charge'].sum().reset_index()
                    df_jour = df_jour.set_index('Date').sort_index()
                    
                    # Fenêtres glissantes
                    fenetre = st.selectbox("Sélectionner la période glissante :", ["7 jours glissants", "5 jours glissants", "3 jours glissants"])
                    jours = 7 if "7" in fenetre else (5 if "5" in fenetre else 3)
                    
                    df_glissant = df_jour.rolling(window=f'{jours}D', min_periods=1).mean()
                    st.line_chart(df_glissant)
            else:
                st.info("Pas assez de données pour afficher les charges.")

        st.markdown("---")
        
        # --- Section Tableaux & Gestion / Poubelles ---
        st.subheader("🌅 Base de données : Forme (Matin)")
        if not st.session_state['db_forme'].empty:
            st.dataframe(st.session_state['db_forme'], use_container_width=True)
            index_a_supprimer_m = st.selectbox("Sélectionner la ligne à supprimer (Matin) :", st.session_state['db_forme'].index, key="del_m")
            if st.button("🗑️ Supprimer cette ligne (Matin)"):
                st.session_state['db_forme'] = st.session_state['db_forme'].drop(index_a_supprimer_m).reset_index(drop=True)
                st.success("Ligne supprimée !")
                st.rerun()
            csv_forme = st.session_state['db_forme'].to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données MATIN (CSV)", data=csv_forme, file_name='forme_matin.csv', mime='text/csv')
        else:
            st.write("Aucune donnée enregistrée.")
        
        st.divider()
        
        st.subheader("🎾 Base de données : Séances & Charges (sRPE)")
        if not st.session_state['db_seances'].empty:
            st.dataframe(st.session_state['db_seances'], use_container_width=True)
            index_a_supprimer_s = st.selectbox("Sélectionner la ligne à supprimer (Séances) :", st.session_state['db_seances'].index, key="del_s")
            if st.button("🗑️ Supprimer cette ligne (Séances)"):
                st.session_state['db_seances'] = st.session_state['db_seances'].drop(index_a_supprimer_s).reset_index(drop=True)
                st.success("Séance supprimée !")
                st.rerun()
            csv_seances = st.session_state['db_seances'].to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données SÉANCES (CSV)", data=csv_seances, file_name='seances_charge.csv', mime='text/csv')
        else:
            st.write("Aucune séance enregistrée.")
        
        st.divider()
        
        st.subheader("🌙 Base de données : Flash Soir")
        if not st.session_state['db_soir'].empty:
            st.dataframe(st.session_state['db_soir'], use_container_width=True)
            index_a_supprimer_soir = st.selectbox("Sélectionner la ligne à supprimer (Soir) :", st.session_state['db_soir'].index, key="del_soir")
            if st.button("🗑️ Supprimer cette ligne (Soir)"):
                st.session_state['db_soir'] = st.session_state['db_soir'].drop(index_a_supprimer_soir).reset_index(drop=True)
                st.success("Bilan supprimé !")
                st.rerun()
            csv_soir = st.session_state['db_soir'].to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données SOIR (CSV)", data=csv_soir, file_name='flash_soir.csv', mime='text/csv')
        else:
            st.write("Aucun bilan du soir enregistré.")
        
    elif saisie_mdp != "":
        st.error("❌ Mot de passe incorrect.")
