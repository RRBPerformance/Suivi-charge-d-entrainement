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

@st.cache_data(ttl=600)
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
        df_forme = pd.DataFrame(columns=['Date', 'Sommeil', 'Fatigue', 'Stress', 'Humeur', 'Score_Forme', 'Douleur_Type', 'Zones_Douleur', 'Whoop_Recup', 'Whoop_Sommeil', 'Whoop_VFC'])
        df_seances = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge', 'Satisfaction'])
        df_soir = pd.DataFrame(columns=['Date', 'Etat_Jour', 'Zones_Douleur_Soir', 'Type_Douleur'])
        df_tests = pd.DataFrame(columns=['Date', 'Periode', 'Test', 'Cote', 'Resultat', 'Unite', 'Objectif_Prochain'])
        return df_forme, df_seances, df_soir, df_tests

def ajouter_ligne(onglet_nom, dico_donnees):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        worksheet.append_row(list(dico_donnees.values()))
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur d'enregistrement Google Sheets : {e}")

def supprimer_ligne_gsheets(onglet_nom, index_ligne):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        worksheet.delete_rows(index_ligne + 2)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur lors de la suppression : {e}")

# Titre principal
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Raph Tennis : Suivi de la Performance</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280;'>Monitoring quotidien - Optimisation et Prévention</p>", unsafe_allow_html=True)
st.divider()

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
    
    st.markdown("### 📡 1. Données de Récupération (Objectif)")
    
    col_btn_m1, col_btn_m2 = st.columns(2)
    with col_btn_m1:
        if st.button("🔄 Synchroniser mon sommeil WHOOP", type="primary", use_container_width=True, key="btn_whoop_matin"):
            st.session_state['whoop_matin_synced'] = True
            st.session_state['sans_montre_matin'] = False
            st.session_state['whoop_recup'] = 76
            st.session_state['whoop_sommeil'] = 93
            st.session_state['whoop_vfc'] = 72
            st.success("✅ Données WHOOP importées avec succès !")
            
    with col_btn_m2:
        if st.button("🤷‍♂️ Je n'ai pas ma montre", use_container_width=True, key="btn_no_montre_matin"):
            st.session_state['sans_montre_matin'] = True
            st.session_state['whoop_matin_synced'] = False

    if st.session_state.get('whoop_matin_synced') or st.session_state.get('sans_montre_matin'):
        st.markdown("---")
        st.markdown("### 🧠 2. Ton Ressenti & Vérification")
        
        date_matin = st.date_input("📅 Date du jour", value=date.today(), key="date_m")
        col1, col2 = st.columns(2)
        
        if st.session_state.get('sans_montre_matin'):
            st.warning("⚠️ Mode manuel activé.")
            with col1:
                sommeil = st.slider("💤 Qualité du sommeil (1-5)", 1, 5, 3)
                fatigue = st.slider("🔋 Niveau de fraîcheur (1-5)", 1, 5, 3)
                recup_corrigee, sommeil_corrige, vfc_corrige = 0, 0, 0
        else:
            st.info("💡 Ajuste si besoin les valeurs affichées par Whoop :")
            with col1:
                recup_corrigee = st.number_input("❤️ Récupération WHOOP (%)", min_value=0, max_value=100, value=int(st.session_state['whoop_recup']))
                sommeil_corrige = st.number_input("💤 Performance Sommeil (%)", min_value=0, max_value=100, value=int(st.session_state['whoop_sommeil']))
                vfc_corrige = st.number_input("🫀 VFC (ms)", min_value=0, value=int(st.session_state['whoop_vfc']))
                
                sommeil = max(1, min(5, round(sommeil_corrige / 20)))
                fatigue = max(1, min(5, round(recup_corrigee / 20)))

        with col2:
            stress = st.slider("🌪️ Niveau de stress (1-5)", 1, 5, 3)
            humeur = st.slider("😊 Humeur (1-5)", 1, 5, 3)
            
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
                'Douleur_Type': type_douleur, 'Zones_Douleur': zones_str,
                'Whoop_Recup': recup_corrigee, 'Whoop_Sommeil': sommeil_corrige, 'Whoop_VFC': vfc_corrige
            }
            ajouter_ligne("Forme", dico)
            st.success(f"🎉 Parfait ! Ton score de forme aujourd'hui est de {score_forme}/20. Enregistré !")
            
            # --- MESSAGE TELEGRAM SYSTEMATIQUE (MATIN) ---
            msg_matin = (
                f"🌅 **Nouveau Check-in Matin - Raph** 🎾\n"
                f"📅 Date : {date_matin}\n"
                f"❤️ Récupération WHOOP : {recup_corrigee}%\n"
                f"💤 Sommeil WHOOP : {sommeil_corrige}%\n"
                f"🫀 VFC : {vfc_corrige} ms\n"
                f"📊 Score Global Forme : {score_forme}/20\n"
                f"⚡ Douleur : {type_douleur} ({zones_str})"
            )
            envoyer_telegram(msg_matin)

            # --- Alertes Supplémentaires ---
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
                        envoyer_telegram(f"🔴 **ALERTE ROUGE FORME**\nChute critique à plus de 2 écarts-types de la moyenne ({moyenne_f:.1f}).")
                    elif z_score_f <= -1:
                        envoyer_telegram(f"🟠 **ALERTE ORANGE FORME**\nBaisse de forme sous la moyenne ({moyenne_f:.1f}).")

            if type_douleur not in ["Aucune", "Courbatures (diffuses)"]:
                envoyer_telegram(f"🚨 **ALERTE MÉDICALE MATIN**\nDouleur signalée : {type_douleur} | Zone : {zones_str}")

            st.session_state.pop('whoop_matin_synced', None)
            st.session_state.pop('sans_montre_matin', None)
            st.rerun()

# --- ONGLET 2 : SÉANCES ---
with tab_seance:
    st.info("⏱️ **Rappel :** À remplir dans les 30 minutes suivant la fin de l'effort.")
    
    st.markdown("### 📡 1. Données de la Montre (Objectif)")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Synchroniser ma montre", type="primary", use_container_width=True):
            st.session_state['whoop_synced'] = True
            st.session_state['sans_montre'] = False
            st.session_state['whoop_strain'] = 14.2  
            st.session_state['whoop_duree'] = 120     
            st.session_state['whoop_type'] = "Tennis (Après-midi)"
            st.success("✅ Données WHOOP importées avec succès !")
            
    with col_btn2:
        if st.button("🤷‍♂️ Je n'ai pas ma montre", use_container_width=True):
            st.session_state['sans_montre'] = True
            st.session_state['whoop_synced'] = False

    if st.session_state.get('whoop_synced') or st.session_state.get('sans_montre'):
        st.markdown("---")
        st.markdown("### 🧠 2. Ton Ressenti & Corrections")
        
        date_seance = st.date_input("📅 Date de la séance", value=date.today(), key="date_s")
        
        if st.session_state.get('sans_montre'):
            st.warning("⚠️ Mode manuel activé.")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                type_final = st.selectbox("Type de séance", ["Échauffement Pré-Match", "Prépa Physique", "Tennis - Entraînement", "Tennis - Match", "Récupération"])
            with col_m2:
                duree_finale = st.number_input("Durée (minutes)", min_value=1, value=90)
            strain_final = 0.0 
        else:
            st.info("💡 Rectifie si besoin l'activité ou la durée ci-dessous :")
            col_w1, col_w2, col_w3 = st.columns(3)
            with col_w1:
                st.metric("Activité brute WHOOP", st.session_state['whoop_type'])
            with col_w2:
                duree_finale = st.number_input("Corriger la durée (min)", min_value=1, value=int(st.session_state['whoop_duree']))
            with col_w3:
                st.metric("Score d'Effort (Strain)", f"{st.session_state['whoop_strain']} / 21")
                
            type_final = st.selectbox("🎯 Définir la vraie nature de la séance :", [
                "Tennis - Match", 
                "Tennis - Entraînement", 
                "Échauffement Pré-Match", 
                "Prépa Physique", 
                "Récupération"
            ], index=0)
            strain_final = st.session_state['whoop_strain']

        col3, col4 = st.columns(2)
        with col3:
            rpe = st.slider("🥵 Difficulté ressentie (RPE 1-10)", 1, 10, 7)
        with col4:
            satisfaction = st.slider("🎯 Satisfaction (1-5)", 1, 5, 3)
            
        st.markdown("#### ⚡ Analyse de la charge")
        charge = duree_finale * rpe

        if st.button("🔥 Enregistrer la séance", use_container_width=True):
            dico_seance = {
                'Date': str(date_seance), 
                'Type': type_final, 
                'Duree': duree_finale, 
                'RPE': rpe, 
                'Charge': charge, 
                'Satisfaction': satisfaction
            }
            ajouter_ligne("Seances", dico_seance)
            st.success(f"📊 Séance validée ! Type : {type_final} | Charge : {charge}.")
            
            # --- MESSAGE TELEGRAM SYSTEMATIQUE (SÉANCE) ---
            msg_seance = (
                f"👟 **Nouvelle Séance Enregistrée - Raph** 🎾\n"
                f"📅 Date : {date_seance}\n"
                f"🏷️ Type : {type_final}\n"
                f"⏱️ Durée : {duree_finale} min\n"
                f"🥵 RPE : {rpe}/10\n"
                f"📈 Charge Totale : {charge} unités\n"
                f"🎯 Satisfaction : {satisfaction}/5"
            )
            envoyer_telegram(msg_seance)

            # --- Alerte Surcharge ---
            df_s_alerte = pd.concat([df_seances, pd.DataFrame([dico_seance])], ignore_index=True)
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
                        envoyer_telegram(f"🔴 **ALERTE ROUGE (Surcharge)**\nPic critique : {derniere_charge:.0f} u (Plus de 2 écarts-types au-dessus de la normale).")
                    elif z_score_c >= 1:
                        envoyer_telegram(f"🟠 **ALERTE ORANGE (Surcharge)**\nCharge élevée : {derniere_charge:.0f} u.")

            st.session_state.pop('whoop_synced', None)
            st.session_state.pop('sans_montre', None)
            st.rerun()

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
        
        # --- MESSAGE TELEGRAM SYSTEMATIQUE (SOIR) ---
        msg_soir = (
            f"🌙 **Flash Soir - Bilan Journalier - Raph** 🎾\n"
            f"📅 Date : {date_soir}\n"
            f"🚦 État : {etat_jour}\n"
            f"⚡ Nature ressenti : {type_soir}\n"
            f"📍 Zone(s) : {zones_soir_str}"
        )
        envoyer_telegram(msg_soir)
        
        if "3" in etat_jour or "4" in etat_jour or type_soir not in ["RAS / Normal", "Musculaire"]:
            envoyer_telegram(f"🚨 **ALERTE MÉDICALE SOIR**\nBilan : {etat_jour} | Douleur : {type_soir} | Zone : {zones_soir_str}")

# --- ONGLET 4 : COACH ---
with tab_coach:
    st.markdown("### 🔐 Espace Réservé au Staff")
    saisie_mdp = st.text_input("Entrez le mot de passe administrateur :", type="password")
    
    if saisie_mdp == MOT_DE_PASSE_COACH:
        st.success("🔓 Accès autorisé.")
        
        df_forme, df_seances, df_soir, df_tests = charger_donnees()
        
        st.markdown("---")
        st.markdown("## 🚨 Tableau de Bord des Alertes (Prévention)")
        col_alerte1, col_alerte2 = st.columns(2)
        with col_alerte1:
            st.markdown("#### 🧠 Alerte État de Forme (7j)")
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
                        st.error(f"🔴 **ALERTE ROUGE** : Score très bas ({dernier_score}/20).")
                    elif z_score_f <= -1:
                        st.warning(f"🟠 **ALERTE ORANGE** : Baisse de forme ({dernier_score}/20).")
                    else:
                        st.success(f"✅ Forme stable (Moyenne : {moyenne_f:.1f}).")
            else:
                st.info("Données insuffisantes (min 3 jours).")
                
        with col_alerte2:
            st.markdown("#### ⚡ Alerte Charge sRPE (21j)")
            if not df_seances.empty and len(df_seances) >= 3:
                df_s = df_seances.copy()
                df_s['Date'] = pd.to_datetime(df_s['Date'])
                df_jour = df_s.groupby('Date')['Charge'].sum().reset_index().sort_values('Date')
                df_jour['Moy_21j'] = df_jour['Charge'].rolling(window=21, min_periods=3).mean()
                df_jour['Std_21j'] = df_jour['Charge'].rolling(window=21, min_periods=3).std()
                derniere_charge = df_jour['Charge'].iloc[-1]
                moyenne_c = df_jour['Moy_21j'].iloc[-1]
                ecart_type_c = df_jour['Std_21j'].iloc[-1]
                if pd.notna(ecart_type_c) and ecart_type_c > 0:
                    z_score_c = (derniere_charge - moyenne_c) / ecart_type_c
                    if z_score_c >= 2:
                        st.error(f"🔴 **SURCHARGE ROUGE** : Pic critique ({derniere_charge:.0f} u).")
                    elif z_score_c >= 1:
                        st.warning(f"🟠 **SURCHARGE ORANGE** : Charge élevée.")
                    else:
                        st.success(f"✅ Charge dans les standards (Moyenne : {moyenne_c:.0f} u).")
            else:
                st.info("Données insuffisantes (min 3 jours).")

        st.markdown("---")
        st.markdown("## 🌅 Base de données : Forme (Matin & WHOOP)")
        if not df_forme.empty:
            st.dataframe(df_forme, use_container_width=True)
            index_a_supprimer_m = st.selectbox("Sélectionner la ligne à supprimer (Matin) :", df_forme.index, key="del_m2")
            if st.button("🗑️ Supprimer cette ligne (Matin)"):
                supprimer_ligne_gsheets("Forme", index_a_supprimer_m)
                st.success("Ligne supprimée !")
                st.rerun()
            csv_forme = df_forme.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données MATIN (CSV)", data=csv_forme, file_name='forme_matin.csv', mime='text/csv')
        
        st.divider()
        st.subheader("🎾 Base de données : Séances & Charges")
        if not df_seances.empty:
            st.dataframe(df_seances, use_container_width=True)
            index_a_supprimer_s = st.selectbox("Sélectionner la ligne à supprimer (Séances) :", df_seances.index, key="del_s2")
            if st.button("🗑️ Supprimer cette ligne (Séances)"):
                supprimer_ligne_gsheets("Seances", index_a_supprimer_s)
                st.success("Séance supprimée !")
                st.rerun()
            csv_seances = df_seances.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données SÉANCES (CSV)", data=csv_seances, file_name='seances_charge.csv', mime='text/csv')
        
        st.divider()
        st.subheader("🌙 Base de données : Flash Soir")
        if not df_soir.empty:
            st.dataframe(df_soir, use_container_width=True)
            index_a_supprimer_soir = st.selectbox("Sélectionner la ligne à supprimer (Soir) :", df_soir.index, key="del_soir2")
            if st.button("🗑️ Supprimer cette ligne (Soir)"):
                supprimer_ligne_gsheets("Soir", index_a_supprimer_soir)
                st.success("Bilan supprimé !")
                st.rerun()
            csv_soir = df_soir.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Télécharger données SOIR (CSV)", data=csv_soir, file_name='flash_soir.csv', mime='text/csv')
        
    elif saisie_mdp != "":
        st.error("❌ Mot de passe incorrect.")
