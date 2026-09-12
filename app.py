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
import requests

# Configuration de la page
st.set_page_config(page_title="Suivi de Charge RRB", page_icon="🎾", layout="wide")

# Mot de passe sécurisé
MOT_DE_PASSE_COACH = "RomainRB2004!"

# --- FONCTION TELEGRAM ---
def envoyer_telegram(message):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": str(chat_id), "text": message}
        reponse = requests.post(url, json=payload)
        
        # Si Telegram refuse le message, on affiche l'erreur en rouge sur Streamlit
        if reponse.status_code != 200:
            st.error(f"❌ Telegram a bloqué l'envoi. Raison : {reponse.text}")
            
    except Exception as e:
        st.error(f"❌ Erreur de configuration Telegram : {e}")

# --- CONNEXION GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("RaphSuivi_Tennis_Database")
    return sheet

def charger_donnees():
    try:
        sh = init_connection()
        df_forme = pd.DataFrame(sh.worksheet("Forme").get_all_records())
        df_seances = pd.DataFrame(sh.worksheet("Seances").get_all_records())
        df_soir = pd.DataFrame(sh.worksheet("Soir").get_all_records())
        
        try:
            df_tests = pd.DataFrame(sh.worksheet("Tests").get_all_records())
        except Exception:
            df_tests = pd.DataFrame(columns=['Date', 'Periode', 'Test', 'Cote', 'Resultat', 'Unite', 'Objectif_Prochain'])
            
        return df_forme, df_seances, df_soir, df_tests
    except Exception as e:
        df_forme = pd.DataFrame(columns=['Date', 'Sommeil', 'Fatigue', 'Stress', 'Humeur', 'Score_Forme', 'Douleur_Type', 'Zones_Douleur'])
        df_seances = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge', 'Satisfaction'])
        df_soir = pd.DataFrame(columns=['Date', 'Etat_Jour', 'Zones_Douleur_Soir', 'Type_Douleur'])
        df_tests = pd.DataFrame(columns=['Date', 'Periode', 'Test', 'Cote', 'Resultat', 'Unite', 'Objectif_Prochain'])
        return df_forme, df_seances, df_soir, df_tests

def ajouter_ligne(onglet_nom, dico_donnees):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        if len(worksheet.get_all_values()) == 0:
            worksheet.append_row(list(dico_donnees.keys()))
        worksheet.append_row(list(dico_donnees.values()))
    except Exception as e:
        st.error(f"Erreur d'enregistrement Google Sheets : {e}")

def supprimer_ligne_gsheets(onglet_nom, index_ligne):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        worksheet.delete_rows(index_ligne + 2)
    except Exception as e:
        st.error(f"Erreur lors de la suppression : {e}")

# Titre principal
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Raph Tennis : Suivi de la Performance</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280;'>Monitoring quotidien - Optimisation et Prévention</p>", unsafe_allow_html=True)
st.divider()

# Chargement global des données
df_forme, df_seances, df_soir, df_tests = charger_donnees()

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
        
        df_f_alerte = pd.concat([df_forme, pd.DataFrame([dico])], ignore_index=True)
        df_f_alerte['Score_Forme'] = pd.to_numeric(df_f_alerte['Score_Forme'])
        if len(df_f_alerte) >= 3:
            df_f_alerte['Date'] = pd.to_datetime(df_f_alerte['Date'])
            df_f_alerte = df_f_alerte.sort_values('Date')
            df_f_alerte['Moy_7j'] = df_f_alerte['Score_Forme'].rolling(window=7, min_periods=3).mean()
            df_f_alerte['Std_7j'] = df_f_alerte['Score_Forme'].rolling(window=7, min_periods=3).std()
            
            moyenne_f = df_f_alerte['Moy_7j'].iloc[-1]
            ecart_type_f = df_f_alerte['Std_7j'].iloc[-1]
            
            if pd.notna(ecart_type_f) and ecart_type_f > 0:
                z_score_f = (score_forme - moyenne_f) / ecart_type_f
                
                if z_score_f <= -2:
                    envoyer_telegram(f"🔴 ALERTE ROUGE FORME - Raph 🎾\nScore très bas ({score_forme}/20).\nChute à plus de 2 écarts-types de sa moyenne ({moyenne_f:.1f}). Fatigue centrale suspectée.")
                elif z_score_f <= -1:
                    envoyer_telegram(f"🟠 ALERTE ORANGE FORME - Raph 🎾\nBaisse de forme ({score_forme}/20).\nÀ plus de 1 écart-type sous sa moyenne ({moyenne_f:.1f}). Adapter l'échauffement.")

        if type_douleur not in ["Aucune", "Courbatures (diffuses)"]:
            envoyer_telegram(f"🚨 ALERTE MÉDICALE MATIN - Raph 🎾\nDouleur signalée : {type_douleur}\nZone(s) : {zones_str}")

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
        
        df_s_alerte = pd.concat([df_seances, pd.DataFrame([dico])], ignore_index=True)
        df_s_alerte['Date'] = pd.to_datetime(df_s_alerte['Date'])
        df_s_alerte['Charge'] = pd.to_numeric(df_s_alerte['Charge'])
        
        df_jour = df_s_alerte.groupby('Date')['Charge'].sum().reset_index().sort_values('Date')
        
        if len(df_jour) >= 3:
            df_jour['Moy_21j'] = df_jour['Charge'].rolling(window=21, min_periods=3).mean()
            df_jour['Std_21j'] = df_jour['Charge'].rolling(window=21, min_periods=3).std()
            
            derniere_charge = df_jour['Charge'].iloc[-1]
            moyenne_c = df_jour['Moy_21j'].iloc[-1]
            ecart_type_c = df_jour['Std_21j'].iloc[-1]
            
            if pd.notna(ecart_type_c) and ecart_type_c > 0:
                z_score_c = (derniere_charge - moyenne_c) / ecart_type_c
                
                if z_score_c >= 2:
                    envoyer_telegram(f"🔴 ALERTE ROUGE (Surcharge) - Raph 🎾\nPic critique de charge : {derniere_charge:.0f} u !\nPlus de 2 écarts-types au-dessus de la normale ({moyenne_c:.0f} u). Grand risque tissulaire.")
                elif z_score_c >= 1:
                    envoyer_telegram(f"🟠 ALERTE ORANGE (Surcharge) - Raph 🎾\nCharge très élevée : {derniere_charge:.0f} u.\nPlus de 1 écart-type au-dessus de la moyenne ({moyenne_c:.0f} u).")

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
        
        if "3" in etat_jour or "4" in etat_jour or type_soir not in ["RAS / Normal", "Musculaire"]:
            envoyer_telegram(f"🚨 ALERTE MÉDICALE SOIR - Raph 🎾\nBilan : {etat_jour}\nDouleur : {type_soir}\nZone(s) : {zones_soir_str}")

# --- ONGLET 4 : COACH ---
with tab_coach:
    st.markdown("### 🔐 Espace Réservé au Staff")
    saisie_mdp = st.text_input("Entrez le mot de passe administrateur :", type="password")
    
    if saisie_mdp == MOT_DE_PASSE_COACH:
        st.success("🔓 Accès autorisé.")
        
        # ==========================================
        # 🚨 SYSTÈME D'ALERTES Z-SCORE (Écart-type)
        # ==========================================
        st.markdown("---")
        st.markdown("## 🚨 Tableau de Bord des Alertes (Prévention des Blessures)")
        
        col_alerte1, col_alerte2 = st.columns(2)
        
        with col_alerte1:
            st.markdown("#### 🧠 Alerte État de Forme (7 derniers jours)")
            if not df_forme.empty and len(df_forme) >= 3:
                df_f = df_forme.copy()
                df_f['Date'] = pd.to_datetime(df_f['Date'])
                df_f = df_f.sort_values('Date')
                
                df_f['Moy_7j'] = df_f['Score_Forme'].rolling(window=7, min_periods=3).mean()
                df_f['Std_7j'] = df_f['Score_Forme'].rolling(window=7, min_periods=3).std()
                
                dernier_score = df_f['Score_Forme'].iloc[-1]
                moyenne_f = df_f['Moy_7j'].iloc[-1]
                ecart_type_f = df_f['Std_7j'].iloc[-1]
                
                if pd.notna(ecart_type_f) and ecart_type_f > 0:
                    z_score_f = (dernier_score - moyenne_f) / ecart_type_f
                    
                    if z_score_f <= -2:
                        st.error(f"🔴 **ALERTE ROUGE** : Score très bas ({dernier_score}/20). Chute critique à plus de 2 écarts-types de la moyenne ({moyenne_f:.1f}). Fatigue centrale suspectée.")
                    elif z_score_f <= -1:
                        st.warning(f"🟠 **ALERTE ORANGE** : Baisse de forme ({dernier_score}/20). À plus de 1 écart-type sous la moyenne ({moyenne_f:.1f}). Adapter l'échauffement.")
                    elif z_score_f >= 1:
                        st.success(f"🟢 **EXCELLENT** : Forme optimale ({dernier_score}/20). Supérieure à la moyenne récente.")
                    else:
                        st.info(f"✅ Forme stable et dans la norme (Moyenne : {moyenne_f:.1f}).")
                else:
                    st.info("Calcul en cours, attente de variations des scores...")
            else:
                st.info("Pas assez de données pour l'analyse de forme (minimum 3 jours nécessaires).")
                
        with col_alerte2:
            st.markdown("#### ⚡ Alerte Charge sRPE (21 derniers jours)")
            if not df_seances.empty and len(df_seances) >= 3:
                df_s = df_seances.copy()
                df_s['Date'] = pd.to_datetime(df_s['Date'])
                
                df_jour = df_s.groupby('Date')['Charge'].sum().reset_index()
                df_jour = df_jour.sort_values('Date')
                
                df_jour['Moy_21j'] = df_jour['Charge'].rolling(window=21, min_periods=3).mean()
                df_jour['Std_21j'] = df_jour['Charge'].rolling(window=21, min_periods=3).std()
                
                derniere_charge = df_jour['Charge'].iloc[-1]
                moyenne_c = df_jour['Moy_21j'].iloc[-1]
                ecart_type_c = df_jour['Std_21j'].iloc[-1]
                
                if pd.notna(ecart_type_c) and ecart_type_c > 0:
                    z_score_c = (derniere_charge - moyenne_c) / ecart_type_c
                    
                    if z_score_c >= 2:
                        st.error(f"🔴 **ALERTE ROUGE (Surcharge)** : Pic critique ({derniere_charge:.0f} u) ! Plus de 2 écarts-types au-dessus de la normale ({moyenne_c:.0f} u). Grand risque de blessure tissulaire.")
                    elif z_score_c >= 1:
                        st.warning(f"🟠 **ALERTE ORANGE (Surcharge)** : Charge élevée ({derniere_charge:.0f} u). Plus de 1 écart-type au-dessus de la moyenne. Surveiller la récupération.")
                    elif z_score_c <= -2:
                        st.error(f"🔴 **ALERTE ROUGE (Sous-charge)** : Baisse critique de charge ({derniere_charge:.0f} u). Plus de 2 écarts-types sous la moyenne. Risque de désentraînement si prolongé.")
                    elif z_score_c <= -1:
                        st.warning(f"🟠 **ALERTE ORANGE (Sous-charge)** : Charge très faible ({derniere_charge:.0f} u). Phase d'affûtage ou anomalie ?")
                    else:
                        st.info(f"✅ Charge quotidienne dans les standards habituels (Moyenne : {moyenne_c:.0f} u).")
                else:
                    st.info("Calcul en cours, attente de variations des charges...")
            else:
                st.info("Pas assez de données pour l'analyse de charge (minimum 3 jours nécessaires).")
                
        # ==========================================

        st.markdown("---")
        st.markdown("## 🏋️‍♂️ Suivi des Évaluations Physiques (Tests)")
        
        with st.expander("➕ Saisir un nouveau résultat de Test"):
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                date_test = st.date_input("Date du test", value=date.today(), key="d_test")
                periode = st.selectbox("Période d'évaluation", ["Test Initial (Septembre)", "Test Intermédiaire (Hiver)", "Test Final (Printemps)"])
                
                nom_test = st.selectbox("Type de Test", [
                    "VMA", "Sprint 10m", "Suicide", "Taille", "Taille bras levés", "Poids", "Envergure",
                    "Mobilité - Cheville", "Mobilité - Ischio (doigt par terre)", "Mobilité - Quadri (touche fesse)",
                    "Mobilité - Épaule à 90°", "Mobilité - Épaule bras tendus", "Test cognitif",
                    "Triple saut sur 1 pied sans élan", "Tour de 4 plots aller-retour (5m d'écart)"
                ])
                cote = st.selectbox("Côté / Jambe (si applicable)", ["Aucun / Bilatéral", "Droite", "Gauche"])
                
            with col_t2:
                resultat = st.number_input("Résultat obtenu", format="%.2f", step=0.1)
                unite = st.text_input("Unité (ex: sec, cm, kg, palier)")
                objectif = st.text_input("Objectif fixé pour le prochain test")
                
            if st.button("💾 Enregistrer le résultat du Test", use_container_width=True):
                dico_test = {
                    'Date': str(date_test), 'Periode': periode, 'Test': nom_test, 'Cote': cote, 
                    'Resultat': resultat, 'Unite': unite, 'Objectif_Prochain': objectif
                }
                ajouter_ligne("Tests", dico_test)
                st.success("Résultat de test enregistré avec succès !")
                st.rerun()

        if not df_tests.empty:
            st.dataframe(df_tests, use_container_width=True)
            index_a_supprimer_t = st.selectbox("Sélectionner la ligne à supprimer (Tests) :", df_tests.index, key="del_t")
            if st.button("🗑️ Supprimer ce test"):
                supprimer_ligne_gsheets("Tests", index_a_supprimer_t)
                st.success("Test supprimé du Google Sheets !")
                st.rerun()
            csv_tests = df_tests.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger la base TESTS (CSV)", data=csv_tests, file_name='tests_physiques.csv', mime='text/csv')
        else:
            st.info("Aucun résultat de test n'a encore été enregistré.")

        st.markdown("---")
        st.markdown("## 📈 Tableaux de Bord & Sommes Glissantes de Charge")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📉 Évolution du Score de Forme (Matin)")
            if not df_forme.empty and 'Score_Forme' in df_forme.columns:
                df_f_chart = df_forme.copy()
                df_f_chart['Date'] = pd.to_datetime(df_f_chart['Date'])
                df_f_chart = df_f_chart.set_index('Date')[['Score_Forme']]
                
                # NOUVEAUTÉ : Formatage strict de l'index en date pour supprimer l'axe des heures
                df_f_chart.index = df_f_chart.index.date
                
                st.line_chart(df_f_chart)
            else:
                st.info("Pas assez de données pour afficher le graphique de forme.")
                
        with col_g2:
            st.subheader("📊 Somme Cumulative Glissante (Charge sRPE)")
            if not df_seances.empty and 'Charge' in df_seances.columns:
                vue_charge = st.radio("Mode d'affichage des charges :", ["Séances par type (Empilé)", "Somme cumulative (3j / 7j / 21j)"], horizontal=True)
                
                df_s = df_seances.copy()
                df_s['Date'] = pd.to_datetime(df_s['Date'])
                
                if vue_charge == "Séances par type (Empilé)":
                    df_pivot = df_s.pivot_table(index='Date', columns='Type', values='Charge', aggfunc='sum').fillna(0)
                    
                    # NOUVEAUTÉ : Formatage strict de l'index en date pour supprimer l'axe des heures
                    df_pivot.index = df_pivot.index.date
                    
                    st.bar_chart(df_pivot)
                else:
                    fenetre = st.selectbox("Sélectionner la période glissante :", ["3 jours glissants", "7 jours glissants", "21 jours glissants"])
                    jours = 21 if "21" in fenetre else (7 if "7" in fenetre else 3)
                    
                    df_jour = df_s.groupby('Date')['Charge'].sum().reset_index()
                    df_jour = df_jour.set_index('Date').sort_index()
                    
                    df_glissant = df_jour.rolling(window=f'{jours}D', min_periods=1).sum()
                    
                    val_max = df_glissant['Charge'].max()
                    val_min = df_glissant['Charge'].min()
                    
                    df_glissant['Somme Max (Plafond)'] = val_max
                    df_glissant['Somme Min (Plancher)'] = val_min
                    
                    # NOUVEAUTÉ : Formatage strict de l'index en date pour supprimer l'axe des heures
                    df_glissant.index = df_glissant.index.date
                    
                    st.line_chart(df_glissant)
                    
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.metric(label=f"🔴 Somme Max glissante ({jours}j)", value=f"{val_max:.1f} u")
                    with col_info2:
                        st.metric(label=f"🟢 Somme Min glissante ({jours}j)", value=f"{val_min:.1f} u")
            else:
                st.info("Pas assez de données pour afficher les charges.")

        st.markdown("---")
        
        st.subheader("🌅 Base de données : Forme (Matin)")
        if not df_forme.empty:
            st.dataframe(df_forme, use_container_width=True)
            index_a_supprimer_m = st.selectbox("Sélectionner la ligne à supprimer (Matin) :", df_forme.index, key="del_m2")
            if st.button("🗑️ Supprimer cette ligne (Matin)"):
                supprimer_ligne_gsheets("Forme", index_a_supprimer_m)
                st.success("Ligne supprimée du Google Sheets !")
                st.rerun()
        
        st.divider()
        
        st.subheader("🎾 Base de données : Séances & Charges (sRPE)")
        if not df_seances.empty:
            st.dataframe(df_seances, use_container_width=True)
            index_a_supprimer_s = st.selectbox("Sélectionner la ligne à supprimer (Séances) :", df_seances.index, key="del_s2")
            if st.button("🗑️ Supprimer cette ligne (Séances)"):
                supprimer_ligne_gsheets("Seances", index_a_supprimer_s)
                st.success("Séance supprimée du Google Sheets !")
                st.rerun()
        
        st.divider()
        
        st.subheader("🌙 Base de données : Flash Soir")
        if not df_soir.empty:
            st.dataframe(df_soir, use_container_width=True)
            index_a_supprimer_soir = st.selectbox("Sélectionner la ligne à supprimer (Soir) :", df_soir.index, key="del_soir2")
            if st.button("🗑️ Supprimer cette ligne (Soir)"):
                supprimer_ligne_gsheets("Soir", index_a_supprimer_soir)
                st.success("Bilan supprimé du Google Sheets !")
                st.rerun()
        
    elif saisie_mdp != "":
        st.error("❌ Mot de passe incorrect.")
