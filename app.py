#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 14:27:14 2026

@author: romainromeyerbouchard
"""

import streamlit as st
import pandas as pd
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuration de la page
st.set_page_config(page_title="Suivi de Charge RRB", page_icon="🎾", layout="wide")

# Mot de passe sécurisé
MOT_DE_PASSE_COACH = "RomainRB2004!"

# --- CONNEXION GOOGLE SHEETS ---
@st.cache_resource
init_connection():
    # Connexion sécurisée via les secrets Streamlit
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Ouvre le Google Sheets par son nom
    sheet = client.open("Suivi_Tennis_Database")
    return sheet

# Fonction pour charger les données depuis Google Sheets
def charger_donnees():
    try:
        sh = init_connection()
        df_forme = pd.DataFrame(sh.worksheet("Forme").get_all_records())
        df_seances = pd.DataFrame(sh.worksheet("Seances").get_all_records())
        df_soir = pd.DataFrame(sh.worksheet("Soir").get_all_records())
        return df_forme, df_seances, df_soir
    except Exception as e:
        # Si les onglets sont vides au début, on renvoie des dataframes vides bien structurés
        df_forme = pd.DataFrame(columns=['Date', 'Sommeil', 'Fatigue', 'Stress', 'Humeur', 'Score_Forme', 'Douleur_Type', 'Zones_Douleur'])
        df_seances = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge', 'Satisfaction'])
        df_soir = pd.DataFrame(columns=['Date', 'Etat_Jour', 'Zones_Douleur_Soir', 'Type_Douleur'])
        return df_forme, df_seances, df_soir

# Fonction pour ajouter une ligne dans Google Sheets
def ajouter_ligne(onglet_nom, dico_donnees):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        # Si l'onglet est totalement vide, on ajoute les en-têtes d'abord
        if len(worksheet.get_all_values()) == 0:
            worksheet.append_row(list(dico_donnees.keys()))
        worksheet.append_row(list(dico_donnees.values()))
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement dans Google Sheets : {e}")

# Fonction pour supprimer une ligne dans Google Sheets
def supprimer_ligne_gsheets(onglet_nom, index_ligne):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        # Les lignes dans gspread commencent à 2 (ligne 1 = en-têtes)
        worksheet.delete_rows(index_ligne + 2)
    except Exception as e:
        st.error(f"Erreur lors de la suppression : {e}")

# Titre principal
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Académie Tennis : Suivi de la Performance</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280;'>Monitoring quotidien - Optimisation et Prévention</p>", unsafe_allow_html=True)
st.divider()

tab_matin, tab_seance, tab_soir, tab_coach = st.tabs(["🌅 Check-in Matin", "👟 Bilan Séance", "🌙 Flash Soir", "🔐 Espace Coach"])

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
        
        dico = {
            'Date': str(date_matin), 'Sommeil': sommeil, 'Fatigue': fatigue, 
            'Stress': stress, 'Humeur': humeur, 'Score_Forme': score_forme,
            'Douleur_Type': type_douleur, 'Zones_Douleur': zones_str
        }
        ajouter_ligne("Forme", dico)
        st.success(f"🎉 Parfait ! Ton score de forme aujourd'hui est de {score_forme}/20. Enregistré !")

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
        dico = {
            'Date': str(date_seance), 'Type': type_seance, 'Duree': duree, 
            'RPE': rpe, 'Charge': charge, 'Satisfaction': satisfaction
        }
        ajouter_ligne("Seances", dico)
        st.success(f"📊 Séance validée ! Charge calculée : {charge} unités. Enregistrée !")

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
        dico = {
            'Date': str(date_soir), 'Etat_Jour': etat_jour, 
            'Zones_Douleur_Soir': zones_soir_str, 'Type_Douleur': type_soir
        }
        ajouter_ligne("Soir", dico)
        st.success("✅ Bilan du soir enregistré dans la base de données commune !")

# --- ONGLET 4 : COACH AVEC GOOGLE SHEETS ---
with tab_coach:
    st.markdown("### 🔐 Espace Réservé au Staff")
    saisie_mdp = st.text_input("Entrez le mot de passe administrateur :", type="password")
    
    if saisie_mdp == MOT_DE_PASSE_COACH:
        st.success("🔓 Accès autorisé.")
        
        # Charger les données en direct depuis Google Sheets
        df_forme, df_seances, df_soir = charger_donnees()
        
        st.markdown("---")
        st.markdown("## 📈 Tableaux de Bord & Sommes Glissantes de Charge")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📉 Évolution du Score de Forme (Matin)")
            if not df_forme.empty and 'Score_Forme' in df_forme.columns:
                df_f_chart = df_forme.copy()
                df_f_chart['Date'] = pd.to_datetime(df_f_chart['Date'])
                df_f_chart = df_f_chart.set_index('Date')[['Score_Forme']]
                st.line_chart(df_f_chart)
            else:
                st.info("Pas assez de données pour afficher le graphique de forme.")
                
        with col_g2:
            st.subheader("📊 Somme Cumulative Glissante (Charge sRPE)")
            if not df_seances.empty and 'Charge' in df_seances.columns:
                vue_charge = st.radio("Mode d'affichage des charges :", ["Séances par type (Empilé)", "Somme cumulative (7j / 5j / 3j)"], horizontal=True)
                
                df_s = df_seances.copy()
                df_s['Date'] = pd.to_datetime(df_s['Date'])
                
                if vue_charge == "Séances par type (Empilé)":
                    df_pivot = df_s.pivot_table(index='Date', columns='Type', values='Charge', aggfunc='sum').fillna(0)
                    st.bar_chart(df_pivot)
                else:
                    df_jour = df_s.groupby('Date')['Charge'].sum().reset_index()
                    df_jour = df_jour.set_index('Date').sort_index()
                    
                    fenetre = st.selectbox("Sélectionner la période glissante :", ["7 jours glissants", "5 jours glissants", "3 jours glissants"])
                    jours = 7 if "7" in fenetre else (5 if "5" in fenetre else 3)
                    
                    df_glissant = df_jour.rolling(window=f'{jours}D', min_periods=1).sum()
                    
                    val_max = df_glissant['Charge'].max()
                    val_min = df_glissant['Charge'].min()
                    
                    df_glissant['Somme Max (Plafond)'] = val_max
                    df_glissant['Somme Min (Plancher)'] = val_min
                    
                    st.line_chart(df_glissant)
                    
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.metric(label=f"🔴 Somme Max glissante ({jours}j)", value=f"{val_max:.1f} u")
                    with col_info2:
                        st.metric(label=f"🟢 Somme Min glissante ({jours}j)", value=f"{val_min:.1f} u")
            else:
                st.info("Pas assez de données pour afficher les charges.")

        st.markdown("---")
        
        # --- Section Tableaux & Gestion / Poubelles synchronisées ---
        st.subheader("🌅 Base de données : Forme (Matin)")
        if not df_forme.empty:
            st.dataframe(df_forme, use_container_width=True)
            index_a_supprimer_m = st.selectbox("Sélectionner la ligne à supprimer (Matin) :", df_forme.index, key="del_m")
            if st.button("🗑️ Supprimer cette ligne (Matin)"):
                supprimer_ligne_gsheets("Forme", index_a_supprimer_m)
                st.success("Ligne supprimée du Google Sheets !")
                st.rerun()
            csv_forme = df_forme.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données MATIN (CSV)", data=csv_forme, file_name='forme_matin.csv', mime='text/csv')
        else:
            st.write("Aucune donnée enregistrée.")
        
        st.divider()
        
        st.subheader("🎾 Base de données : Séances & Charges (sRPE)")
        if not df_seances.empty:
            st.dataframe(df_seances, use_container_width=True)
            index_a_supprimer_s = st.selectbox("Sélectionner la ligne à supprimer (Séances) :", df_seances.index, key="del_s")
            if st.button("🗑️ Supprimer cette ligne (Séances)"):
                supprimer_ligne_gsheets("Seances", index_a_supprimer_s)
                st.success("Séance supprimée du Google Sheets !")
                st.rerun()
            csv_seances = df_seances.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données SÉANCES (CSV)", data=csv_seances, file_name='seances_charge.csv', mime='text/csv')
        else:
            st.write("Aucune séance enregistrée.")
        
        st.divider()
        
        st.subheader("🌙 Base de données : Flash Soir")
        if not df_soir.empty:
            st.dataframe(df_soir, use_container_width=True)
            index_a_supprimer_soir = st.selectbox("Sélectionner la ligne à supprimer (Soir) :", df_soir.index, key="del_soir")
            if st.button("🗑️ Supprimer cette ligne (Soir)"):
                supprimer_ligne_gsheets("Soir", index_a_supprimer_soir)
                st.success("Bilan supprimé du Google Sheets !")
                st.rerun()
            csv_soir = df_soir.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données SOIR (CSV)", data=csv_soir, file_name='flash_soir.csv', mime='text/csv')
        else:
            st.write("Aucun bilan du soir enregistré.")
        
    elif saisie_mdp != "":
        st.error("❌ Mot de passe incorrect.")
