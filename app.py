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

# OPTIMISATION : Mise en cache des données pour éviter de saturer l'API Google
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
        df_forme = pd.DataFrame(columns=['Date', 'Sommeil', 'Fatigue', 'Stress', 'Humeur', 'Score_Forme', 'Douleur_Type', 'Zones_Douleur'])
        df_seances = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge', 'Satisfaction'])
        df_soir = pd.DataFrame(columns=['Date', 'Etat_Jour', 'Zones_Douleur_Soir', 'Type_Douleur'])
        df_tests = pd.DataFrame(columns=['Date', 'Periode', 'Test', 'Cote', 'Resultat', 'Unite', 'Objectif_Prochain'])
        return df_forme, df_seances, df_soir, df_tests

def ajouter_ligne(onglet_nom, dico_donnees):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        # On écrit directement sans faire de requête de lecture préalable
        worksheet.append_row(list(dico_donnees.values()))
        # On vide la mémoire cache pour que les graphiques se mettent à jour
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur d'enregistrement Google Sheets : {e}")

def supprimer_ligne_gsheets(onglet_nom, index_ligne):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        worksheet.delete_rows(index_ligne + 2)
        # On vide la mémoire cache pour actualiser la page
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur lors de la suppression : {e}")

# Titre principal
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Raph Tennis : Suivi de la Performance</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280;'>Monitoring quotidien - Optimisation et Prévention</p>", unsafe_allow_html=True)
st.divider()

# Chargement global des données (désormais protégé par le cache)
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
    
    # Deux boutons côte à côte pour le matin
    col_btn_m1, col_btn_m2 = st.columns(2)
    with col_btn_m1:
        if st.button("🔄 Synchroniser mon sommeil WHOOP", type="primary", use_container_width=True, key="btn_whoop_matin"):
            st.session_state['whoop_matin_synced'] = True
            st.session_state['sans_montre_matin'] = False
            # Simulation des données WHOOP du matin
            st.session_state['whoop_recup'] = 82     # % Récupération (Souvent Vert au-dessus de 66%)
            st.session_state['whoop_sommeil'] = 95   # % Sommeil
            st.session_state['whoop_vfc'] = 75       # VFC (HRV) en ms
            st.success("✅ Données WHOOP importées avec succès !")
            
    with col_btn_m2:
        if st.button("🤷‍♂️ Je n'ai pas ma montre", use_container_width=True, key="btn_no_montre_matin"):
            st.session_state['sans_montre_matin'] = True
            st.session_state['whoop_matin_synced'] = False

    # Si l'un des deux boutons a été cliqué, on affiche le questionnaire
    if st.session_state.get('whoop_matin_synced') or st.session_state.get('sans_montre_matin'):
        st.markdown("---")
        st.markdown("### 🧠 2. Ton Ressenti (Subjectif)")
        
        date_matin = st.date_input("📅 Date du jour", value=date.today(), key="date_m")
        col1, col2 = st.columns(2)
        
        # --- MODE SANS MONTRE ---
        if st.session_state.get('sans_montre_matin'):
            st.warning("⚠️ Mode manuel activé : Évalue toi-même ton sommeil et ta fraîcheur physique.")
            with col1:
                sommeil = st.slider("💤 Qualité du sommeil (1=Insomniaque, 5=Parfait)", 1, 5, 3)
                fatigue = st.slider("🔋 Niveau de fraîcheur (1=Épuisé, 5=Frais)", 1, 5, 3)
                
        # --- MODE AVEC MONTRE ---
        else:
            with col1:
                st.metric("❤️ Récupération WHOOP", f"{st.session_state['whoop_recup']} %")
                st.metric("💤 Performance Sommeil", f"{st.session_state['whoop_sommeil']} %")
                st.metric("🫀 VFC (HRV)", f"{st.session_state['whoop_vfc']} ms")
                
                # Conversion discrète des pourcentages WHOOP en score sur 5 pour le Google Sheets
                sommeil = max(1, min(5, round(st.session_state['whoop_sommeil'] / 20)))
                fatigue = max(1, min(5, round(st.session_state['whoop_recup'] / 20)))

        # --- SUITE COMMUNE (Stress, Humeur, Point Clinique) ---
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
        
        # Petite analyse croisée au réveil
        if st.session_state.get('whoop_matin_synced'):
            if st.session_state['whoop_recup'] > 66 and stress <= 2:
                st.warning("⚠️ **Décalage :** Ton corps a bien récupéré physiquement, mais tu te sens stressé ou de mauvaise humeur. C'est sûrement une charge cognitive (pré-match, perso).")
            elif st.session_state['whoop_recup'] < 33 and fatigue >= 4: # Fatigue manuel (ressenti = frais) vs WHOOP (rouge)
                st.warning("⚠️ **Décalage :** Tu te sens en forme, mais ton système nerveux central (VFC) est dans le rouge. L'échauffement devra être très progressif aujourd'hui !")
        
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
            
            # --- Alertes Telegram (On garde votre logique Z-score existante) ---
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

            # Nettoyage pour le prochain jour
            st.session_state.pop('whoop_matin_synced', None)
            st.session_state.pop('sans_montre_matin', None)
            st.rerun()

# --- ONGLET 2 : SÉANCES ---
with tab_seance:
    st.info("⏱️ **Rappel :** À remplir dans les 30 minutes suivant la fin de l'effort.")
    
    st.markdown("### 📡 1. Données de la Montre (Objectif)")
    
    # Deux boutons côte à côte
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Synchroniser ma montre", type="primary", use_container_width=True):
            st.session_state['whoop_synced'] = True
            st.session_state['sans_montre'] = False
            # Simulation des données WHOOP
            st.session_state['whoop_strain'] = 12.5  
            st.session_state['whoop_duree'] = 90     
            st.session_state['whoop_type'] = "Tennis"
            st.success("✅ Données WHOOP importées avec succès !")
            
    with col_btn2:
        if st.button("🤷‍♂️ Je n'ai pas ma montre", use_container_width=True):
            st.session_state['sans_montre'] = True
            st.session_state['whoop_synced'] = False

    # Si l'un des deux boutons a été cliqué, on affiche la suite
    if st.session_state.get('whoop_synced') or st.session_state.get('sans_montre'):
        st.markdown("---")
        st.markdown("### 🧠 2. Ton Ressenti (Subjectif)")
        
        date_seance = st.date_input("📅 Date de la séance", value=date.today(), key="date_s")
        
        # --- MODE SANS MONTRE ---
        if st.session_state.get('sans_montre'):
            st.warning("⚠️ Mode manuel activé : Tu dois renseigner le type et la durée toi-même.")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                type_final = st.selectbox("Type de séance", ["Prépa Physique", "Tennis", "Récupération", "Match"])
            with col_m2:
                duree_finale = st.number_input("Durée (minutes)", min_value=1, value=60)
            strain_final = None # Pas de score WHOOP
            
        # --- MODE AVEC MONTRE ---
        else:
            col_w1, col_w2, col_w3 = st.columns(3)
            with col_w1:
                st.metric("Activité", st.session_state['whoop_type'])
            with col_w2:
                st.metric("Durée (min)", st.session_state['whoop_duree'])
            with col_w3:
                st.metric("Score d'Effort", f"{st.session_state['whoop_strain']} / 21")
                
            type_final = st.session_state['whoop_type']
            duree_finale = st.session_state['whoop_duree']
            strain_final = st.session_state['whoop_strain']

        # --- SUITE COMMUNE (RPE) ---
        col3, col4 = st.columns(2)
        with col3:
            rpe = st.slider("🥵 Difficulté ressentie (RPE 1-10)", 1, 10, 5)
        with col4:
            satisfaction = st.slider("🎯 Satisfaction (1-5)", 1, 5, 3)
            
        st.markdown("#### ⚡ Analyse de la charge")
        charge = duree_finale * rpe
        
        # L'analyse croisée n'est possible que s'il a sa montre
        if st.session_state.get('whoop_synced'):
            strain_sur_10 = (strain_final / 21) * 10
            ecart = rpe - strain_sur_10
            
            if ecart >= 3:
                st.warning("⚠️ **Alerte Fatigue Nerveuse :** Tu as ressenti cette séance comme très dure par rapport à l'impact cardio. Signe possible d'une fatigue neuromusculaire.")
            elif ecart <= -3:
                st.warning("⚠️ **Alerte Surcharge :** La séance t'a paru facile, mais ton organisme a pris un gros impact cardio (Strain élevé).")
            else:
                st.success("✅ **Cohérence parfaite :** Ton ressenti correspond à la dépense mesurée.")
        else:
            st.info("💡 L'analyse croisée avec ton rythme cardiaque n'est pas disponible sans la montre.")

        if st.button("🔥 Enregistrer la séance", use_container_width=True):
            nouvelle_seance = pd.DataFrame({
                'Date': [date_seance], 
                'Type': [type_final], 
                'Duree': [duree_finale], 
                'RPE': [rpe], 
                'Strain_WHOOP': [strain_final],
                'Charge_sRPE': [charge], 
                'Satisfaction': [satisfaction]
            })
            st.session_state['db_seances'] = pd.concat([st.session_state['db_seances'], nouvelle_seance], ignore_index=True)
            st.success(f"📊 Séance validée ! Charge : {charge}.")
            
            # Réinitialisation pour la prochaine séance
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
        
        if "3" in etat_jour or "4" in etat_jour or type_soir not in ["RAS / Normal", "Musculaire"]:
            envoyer_telegram(f"🚨 ALERTE MÉDICALE SOIR - Raph 🎾\nBilan : {etat_jour}\nDouleur : {type_soir}\nZone(s) : {zones_soir_str}")

# --- ONGLET 4 : COACH ---
# --- ONGLET 3 : VUE COACH (SIMULATEUR) ---
with tab_coach:
    st.header("👑 Tableau de bord du Préparateur Physique")
    
    # Génération de fausses données pour la simulation
    import numpy as np
    
    # 1. Simulation des données Matin (30 derniers jours)
    dates_mois = pd.date_range(end=date.today(), periods=30)
    scores_forme = np.random.normal(14, 2, 30).clip(5, 20)
    whoop_recup = np.random.normal(65, 15, 30).clip(10, 100)
    
    df_simul_matin = pd.DataFrame({'Date': dates_mois, 'Score Forme (Subjectif)': scores_forme, 'WHOOP Récup (Objectif)': whoop_recup})
    df_simul_matin.set_index('Date', inplace=True)
    
    # 2. Simulation des données Séances (Charge)
    charge_quotidienne = np.random.normal(400, 150, 30).clip(100, 800)
    df_simul_charge = pd.DataFrame({'Date': dates_mois, 'Charge_Jour': charge_quotidienne})
    df_simul_charge['Charge_Chronique (Lissage 7j)'] = df_simul_charge['Charge_Jour'].rolling(window=7).mean()
    df_simul_charge.set_index('Date', inplace=True)

    # --- AFFICHAGE DES GRAPHIQUES ---
    st.subheader("📈 1. Suivi de la Charge d'Entraînement (sRPE)")
    st.info("Ce graphique permet de comparer la charge du jour avec la charge chronique (moyenne lissée sur 7 jours) pour éviter les pics de fatigue.")
    st.line_chart(df_simul_charge[['Charge_Jour', 'Charge_Chronique (Lissage 7j)']])
    
    st.markdown("---")
    
    st.subheader("🔋 2. Corrélation : Ressenti vs Données WHOOP")
    st.info("Observez si Raph ressent bien sa fatigue. Si la courbe bleue (Ressenti) est haute mais la rouge (WHOOP) s'effondre, c'est une alerte de fatigue nerveuse cachée.")
    st.line_chart(df_simul_matin)
    
    st.markdown("---")
    
    # Indicateurs d'alerte rapides
    st.subheader("🚨 Alertes actives aujourd'hui")
    colA, colB, colC = st.columns(3)
    colA.metric("Charge Hebdo", "3 250 UA", delta="-150 vs sem. dernière", delta_color="normal")
    colB.metric("Moyenne Récup WHOOP", "58 %", delta="-12%", delta_color="inverse")
    colC.warning("Tendinite Épaule (Signalée J-2)")
                
              
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
                
                df_f_chart.index = df_f_chart.index.strftime('%Y-%m-%d')
                
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
                    df_pivot.index = df_pivot.index.strftime('%Y-%m-%d')
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
                    
                    df_glissant.index = df_glissant.index.strftime('%Y-%m-%d')
                    
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
