import streamlit as st
import pandas as pd
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

st.set_page_config(page_title="Suivi de Charge RRB", page_icon="🎾", layout="wide")

MOT_DE_PASSE_COACH = "RomainRB2004!"

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
            
        try:
            df_frais = pd.DataFrame(sh.worksheet("Frais").get_all_records())
            if not df_frais.empty:
                if 'Statut' not in df_frais.columns:
                    df_frais['Statut'] = "Non payé"
                if 'Coach' not in df_frais.columns:
                    df_frais['Coach'] = "Romain"
        except Exception:
            df_frais = pd.DataFrame(columns=['Date', 'Depart', 'Arrivee', 'Distance_km', 'Montant_Euros', 'Statut', 'Coach'])
            
        return df_forme, df_seances, df_soir, df_tests, df_frais
    except Exception as e:
        df_forme = pd.DataFrame(columns=['Date', 'Sommeil', 'Fatigue', 'Stress', 'Humeur', 'Score_Forme', 'Douleur_Type', 'Zones_Douleur'])
        df_seances = pd.DataFrame(columns=['Date', 'Type', 'Contenu_General', 'Duree', 'RPE', 'Charge', 'Satisfaction', 'Contenu', 'Remarques', 'Note_Comportement'])
        df_soir = pd.DataFrame(columns=['Date', 'Etat_Jour', 'Zones_Douleur_Soir', 'Type_Douleur'])
        df_tests = pd.DataFrame(columns=['Date', 'Periode', 'Test', 'Cote', 'Resultat', 'Unite', 'Objectif_Prochain'])
        df_frais = pd.DataFrame(columns=['Date', 'Depart', 'Arrivee', 'Distance_km', 'Montant_Euros', 'Statut', 'Coach'])
        return df_forme, df_seances, df_soir, df_tests, df_frais

def ajouter_ligne(onglet_nom, dico_donnees):
    try:
        sh = init_connection()
        try:
            worksheet = sh.worksheet(onglet_nom)
        except Exception:
            worksheet = sh.add_worksheet(title=onglet_nom, rows="100", cols="20")
            
        en_tetes = worksheet.row_values(1)
        
        if len(en_tetes) == 0:
            worksheet.append_row(list(dico_donnees.keys()))
            en_tetes = list(dico_donnees.keys())
            
        # Construction de la ligne en respectant strictement l'ordre des en-têtes existants dans le Google Sheet
        row_to_append = []
        for header in en_tetes:
            # Recherche de la clé correspondante (gère les synonymes si les anciens noms diffèrent)
            valeur = ""
            if header in dico_donnees:
                valeur = dico_donnees[header]
            else:
                # Correspondances de secours si l'en-tête Google Sheets diffère du dictionnaire Python
                if onglet_nom == "Soir":
                    if header == "Participation du jour" and "Etat_Jour" in dico_donnees:
                        valeur = dico_donnees["Etat_Jour"]
                    elif header == "Localisation de la gêne" and "Zones_Douleur_Soir" in dico_donnees:
                        valeur = dico_donnees["Zones_Douleur_Soir"]
                    elif header == "Nature de la gêne" and "Type_Douleur" in dico_donnees:
                        valeur = dico_donnees["Type_Douleur"]
                
            row_to_append.append(valeur)
            
        worksheet.append_row(row_to_append)
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

def marquer_paye_gsheets(onglet_nom, index_ligne):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        worksheet.update_cell(index_ligne + 2, 6, "Payé")
        worksheet.update_cell(1, 6, "Statut")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur lors du passage en Payé : {e}")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🎾 Raph Tennis : Suivi de la Performance</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280;'>Monitoring quotidien - Optimisation et Prévention</p>", unsafe_allow_html=True)
st.divider()

df_forme, df_seances, df_soir, df_tests, df_frais = charger_donnees()

tab_matin, tab_seance, tab_soir, tab_coach = st.tabs(["🌅 Check-in Matin", "👟 Bilan Séance", "🌙 Flash Soir", "🔐 Espace Coach"])

ZONES_ANATOMIQUES = [
    "Tête / Mâchoire", "Cervicales / Cou", "Trapèzes", "Épaules", "Biceps", "Triceps", "Coudes", 
    "Avant-bras / Poignets / Mains", "Pectoraux", "Dorsaux / Grand dorsal", "Lombaires / Bas du dos", 
    "Abdominaux / Obliques", "Psoas / Ilio-psoas", "Hanches / Adducteurs", "Fessiers", "Quadriceps", 
    "Ischio-jambiers", "Genoux / Rotule", "Mollets (Gros Jumeaux / Soléaire)", "Tendons d'Achille", "Chevilles / Pieds"
]

# ==========================================
# --- ONGLET 1 : MATIN (JOUEUR) ---
# ==========================================
with tab_matin:
    st.info("💡 **Consigne Joueur :** À remplir chaque matin au réveil pour adapter la charge de la journée.")
    
    st.markdown("### 📡 1. Données WHOOP (Saisie Manuelle)")
    st.caption("Recopie les informations affichées sur l'application WHOOP de ton téléphone (laisse à 0 si pas de montre).")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        whoop_recup = st.number_input("🔴/🟢 Score de Récupération (%)", min_value=0, max_value=100, value=0)
        whoop_sommeil = st.number_input("💤 Performance Sommeil (%)", min_value=0, max_value=100, value=0)
    with col_w2:
        whoop_vfc = st.number_input("💓 VFC (Variabilité en ms)", min_value=0, value=0)
        whoop_fc = st.number_input("🫀 FC Repos (bpm)", min_value=0, value=0)
        
    st.markdown("---")
    st.markdown("### 🧠 2. Ton Ressenti (Subjectif)")
    date_matin = st.date_input("📅 Date du jour", value=date.today(), key="date_m")
    col1, col2 = st.columns(2)
    with col1:
        sommeil = st.slider("💤 Qualité du sommeil ressentie (1=Mauvais, 5=Parfait)", 1, 5, 3)
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
            'Douleur_Type': type_douleur, 'Zones_Douleur': zones_str,
            'Whoop_Score': whoop_recup, 'Whoop_VFC': whoop_vfc, 'Whoop_FC': whoop_fc
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

# ==========================================
# --- ONGLET 2 : BILAN SÉANCE (JOUEUR) ---
# ==========================================
with tab_seance:
    st.info("⏱ **Rappel Joueur :** À remplir dans les 30 minutes suivant la fin de l'effort pour consigner tes métriques WHOOP.")
    date_seance_j = st.date_input("📅 Date de la séance", value=date.today(), key="date_sj")
    
    type_seance_j = st.selectbox("🎯 Type de séance :", ["Prépa Physique", "Entraînement Tennis", "Match Officiel", "Match Amical"], key="ts_j")

    st.markdown("### 📡 Données WHOOP (Saisie Joueur)")
    col_wj1, col_wj2, col_wj3, col_wj4 = st.columns(4)
    with col_wj1:
        whoop_strain_j = st.number_input("🔥 Strain (0-21)", min_value=0.0, max_value=21.0, value=0.0, step=0.1, key="ws_j")
    with col_wj2:
        whoop_cal_j = st.number_input("⚡ Énergie (kcal)", min_value=0, value=0, key="wc_j")
    with col_wj3:
        whoop_hr_avg_j = st.number_input("💓 FC Moyenne (bpm)", min_value=0, value=0, key="wha_j")
    with col_wj4:
        whoop_hr_max_j = st.number_input("🚨 FC Max (bpm)", min_value=0, value=0, key="whm_j")

    st.markdown("### 🧠 Ressenti Global & Satisfaction")
    col_rj1, col_rj2 = st.columns(2)
    with col_rj1:
        rpe_j = st.slider("🥵 Difficulté ressentie (RPE 1-10)", 1, 10, 5, key="rpe_j")
    with col_rj2:
        satisfaction_j = st.slider("🎯 Satisfaction (1-5)", 1, 5, 3, key="sat_j")

    if st.button("✅ Valider mon Bilan Séance", use_container_width=True):
        dico_j = {
            'Date': str(date_seance_j),
            'Type': type_seance_j,
            'Contenu_General': "Rempli par le joueur",
            'Duree': 90,
            'RPE': rpe_j,
            'Charge': 90 * rpe_j,
            'Satisfaction': satisfaction_j,
            'Whoop_Strain': whoop_strain_j,
            'Whoop_HR_avg': whoop_hr_avg_j,
            'Whoop_HR_max': whoop_hr_max_j,
            'Whoop_Calories': whoop_cal_j,
            'Contenu': "",
            'Remarques': "",
            'Note_Comportement': ""
        }
        ajouter_ligne("Seances", dico_j)
        st.success("🎯 Bilan de séance enregistré avec succès dans la base commune !")

# ==========================================
# --- ONGLET 3 : SOIR (JOUEUR) ---
# ==========================================
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
        # On utilise les clés exactes correspondant aux colonnes A, B, C, D de votre Google Sheets "Soir"
        dico = {
            'Date': str(date_soir), 
            'Participation du jour': etat_jour, 
            'Localisation de la gêne': zones_soir_str, 
            'Nature de la gêne': type_soir,
            'Etat_Jour': etat_jour,
            'Zones_Douleur_Soir': zones_soir_str,
            'Type_Douleur': type_soir
        }
        ajouter_ligne("Soir", dico)
        st.success("✅ Bilan du soir enregistré dans la base de données commune !")
        
        if "3" in etat_jour or "4" in etat_jour or type_soir not in ["RAS / Normal", "Musculaire"]:
            envoyer_telegram(f"🚨 ALERTE MÉDICALE SOIR - Raph 🎾\nBilan : {etat_jour}\nDouleur : {type_soir}\nZone(s) : {zones_soir_str}")

# ==========================================
# --- ONGLET 4 : ESPACE COACH (STAFF) ---
# ==========================================
with tab_coach:
    st.markdown("### 🔐 Accès Espace Staff")
    saisie_mdp = st.text_input("Entrez le mot de passe administrateur :", type="password")
    
    if saisie_mdp == MOT_DE_PASSE_COACH:
        st.success("🔓 Accès autorisé.")
        
        df_forme, df_seances, df_soir, df_tests, df_frais = charger_donnees()
        
        tab_c_dash, tab_c_romain, tab_c_luca, tab_c_admin = st.tabs([
            "📊 Alertes & Dashboards", 
            "🏋️‍♂️ Pôle Physique (Romain)", 
            "🎾 Pôle Tennis (Luca)", 
            "🚗 Frais & Administration"
        ])
        
        # --- SOUS-ONGLET 1 : DASHBOARDS & ALERTES ---
        with tab_c_dash:
            st.markdown("## 🚨 Tableau de Bord des Alertes")
            col_alerte1, col_alerte2 = st.columns(2)
            
            with col_alerte1:
                st.markdown("#### 🧠 Alerte État de Forme")
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
                            st.error(f"🔴 **ALERTE ROUGE** : Score bas ({dernier_score}/20).")
                        elif z_score_f <= -1:
                            st.warning(f"🟠 **ALERTE ORANGE** : Baisse de forme ({dernier_score}/20).")
                        elif z_score_f >= 1:
                            st.success(f"🟢 **EXCELLENT** : Forme optimale ({dernier_score}/20).")
                        else:
                            st.info(f"✅ Forme stable et dans la norme (Moyenne : {moyenne_f:.1f}).")
                    else:
                        st.info("Calcul en cours...")
                else:
                    st.info("Pas assez de données pour l'analyse.")
                    
            with col_alerte2:
                st.markdown("#### ⚡ Charge sRPE")
                if not df_seances.empty and len(df_seances) >= 3:
                    df_s = df_seances.copy()
                    df_s['Date'] = pd.to_datetime(df_s['Date'])
                    df_jour = df_s.groupby('Date')['Charge'].sum().reset_index().set_index('Date').sort_index()
                    
                    idx_alerte = pd.date_range(start=df_jour.index.min(), end=pd.to_datetime(date.today()))
                    df_jour = df_jour.reindex(idx_alerte, fill_value=0)
                    
                    df_jour['Moy_21j'] = df_jour['Charge'].rolling(window=21, min_periods=3).mean()
                    df_jour['Std_21j'] = df_jour['Charge'].rolling(window=21, min_periods=3).std()
                    derniere_charge = df_jour['Charge'].iloc[-1]
                    moyenne_c = df_jour['Moy_21j'].iloc[-1]
                    ecart_type_c = df_jour['Std_21j'].iloc[-1]
                    
                    if pd.notna(ecart_type_c) and ecart_type_c > 0:
                        z_score_c = (derniere_charge - moyenne_c) / ecart_type_c
                        if z_score_c >= 2:
                            st.error(f"🔴 **ALERTE ROUGE (Surcharge)** : Pic critique ({derniere_charge:.0f} u) !")
                        elif z_score_c >= 1:
                            st.warning(f"🟠 **ALERTE ORANGE (Surcharge)** : Charge élevée ({derniere_charge:.0f} u).")
                        elif z_score_c <= -2:
                            st.error(f"🔴 **ALERTE ROUGE (Sous-charge)** : Baisse critique de charge ({derniere_charge:.0f} u).")
                        elif z_score_c <= -1:
                            st.warning(f"🟠 **ALERTE ORANGE (Sous-charge)** : Charge très faible ({derniere_charge:.0f} u).")
                        else:
                            st.info(f"✅ Charge quotidienne dans les standards habituels.")
                    else:
                        st.info("Calcul en cours...")
                else:
                    st.info("Pas assez de données pour l'analyse.")

            st.markdown("---")
            st.markdown("## 📈 Tableaux de Bord & Sommes Glissantes")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.subheader("📉 Évolution du Score de Forme")
                if not df_forme.empty and 'Score_Forme' in df_forme.columns:
                    df_f_chart = df_forme.copy()
                    df_f_chart['Date'] = pd.to_datetime(df_f_chart['Date'])
                    df_f_chart = df_f_chart.set_index('Date')[['Score_Forme']]
                    df_f_chart.index = df_f_chart.index.strftime('%Y-%m-%d')
                    st.line_chart(df_f_chart)
                else:
                    st.info("Pas assez de données.")
            with col_g2:
                st.subheader("📊 Charge sRPE")
                if not df_seances.empty and 'Charge' in df_seances.columns:
                    vue_charge = st.radio("Affichage :", ["Séances (Empilé)", "Somme cumulative"], horizontal=True)
                    df_s = df_seances.copy()
                    df_s['Date'] = pd.to_datetime(df_s['Date'])
                    if vue_charge == "Séances (Empilé)":
                        df_pivot = df_s.pivot_table(index='Date', columns='Type', values='Charge', aggfunc='sum').fillna(0)
                        idx_pivot = pd.date_range(start=df_pivot.index.min(), end=pd.to_datetime(date.today()))
                        df_pivot = df_pivot.reindex(idx_pivot, fill_value=0)
                        df_pivot.index = df_pivot.index.strftime('%Y-%m-%d')
                        st.bar_chart(df_pivot)
                    else:
                        df_jour = df_s.groupby('Date')['Charge'].sum().reset_index().set_index('Date').sort_index()
                        idx_jour = pd.date_range(start=df_jour.index.min(), end=pd.to_datetime(date.today()))
                        df_jour = df_jour.reindex(idx_jour, fill_value=0)
                        df_glissant = df_jour.rolling(window='7D', min_periods=1).sum()
                        df_glissant.index = df_glissant.index.strftime('%Y-%m-%d')
                        st.line_chart(df_glissant)
                else:
                    st.info("Pas assez de données.")

            st.markdown("---")
            st.markdown("## 🧠 Analyse Avancée : Ressenti (sRPE) vs Réel (WHOOP)")
            if not df_seances.empty and 'Whoop_Strain' in df_seances.columns:
                df_plot = df_seances[pd.to_numeric(df_seances['Whoop_Strain'], errors='coerce') > 0].copy()
                if not df_plot.empty:
                    df_plot['RPE'] = pd.to_numeric(df_plot['RPE'])
                    df_plot['Whoop_Strain'] = pd.to_numeric(df_plot['Whoop_Strain'])
                    df_plot['Strain (sur 10)'] = (df_plot['Whoop_Strain'] / 21) * 10
                    df_graph = df_plot.set_index('Date').sort_index()
                    st.markdown("#### 📈 Évolution de la difficulté (RPE vs Strain)")
                    st.line_chart(df_graph[['RPE', 'Strain (sur 10)']])
                    df_plot['Ecart'] = df_plot['RPE'] - df_plot['Strain (sur 10)']
                    ecart_moyen = df_plot['Ecart'].mean()
                    col_c1, col_c2, col_c3 = st.columns(3)
                    col_c1.metric("Moyenne RPE (Ressenti)", f"{df_plot['RPE'].mean():.1f} / 10")
                    col_c2.metric("Moyenne Strain (Cardio)", f"{df_plot['Whoop_Strain'].mean():.1f} / 21")
                    if ecart_moyen > 2:
                        col_c3.metric("Tendance", "Surcharge Nerveuse ⚠️")
                        st.warning("🚨 **Alerte Coach :** Raph perçoit les séances comme étant beaucoup plus dures que ce que son cœur indique.")
                    elif ecart_moyen < -2:
                        col_c3.metric("Tendance", "Sous-évaluation 📉")
                        st.info("💡 **Info Coach :** Le système cardio travaille très fort, mais Raph trouve la séance facile.")
                    else:
                        col_c3.metric("Tendance", "Cohérence Parfaite ✅")
                        st.success("🎯 **Info Coach :** Son ressenti correspond exactement au coût physiologique.")
                else:
                    st.info("⏳ Aucune séance avec les données Whoop n'a encore été enregistrée.")
            else:
                st.info("⏳ Les données Whoop s'afficheront ici une fois la première séance enregistrée.")

            # --- HISTORIQUE DES CHECK-INS MATIN & SOIR ---
            st.markdown("---")
            st.markdown("## 📋 Historique des Check-ins Joueur (Matin & Soir)")
            col_hist1, col_hist2 = st.columns(2)
            
            with col_hist1:
                st.subheader("🌅 Historique - Check-in Matin")
                if not df_forme.empty:
                    df_f_hist = df_forme.sort_values(by='Date', ascending=False)
                    for idx, row in df_f_hist.iterrows():
                        with st.expander(f"📅 {row['Date']} - Score Forme : {row.get('Score_Forme', 'N/C')}/20"):
                            st.markdown(f"**Sommeil :** {row.get('Sommeil', 'N/C')} | **Fraîcheur :** {row.get('Fatigue', 'N/C')} | **Stress :** {row.get('Stress', 'N/C')} | **Humeur :** {row.get('Humeur', 'N/C')}")
                            st.markdown(f"**Douleur / Gêne :** {row.get('Douleur_Type', 'Aucune')} ({row.get('Zones_Douleur', 'Aucune')})")
                            st.markdown(f"**Whoop :** Récup : {row.get('Whoop_Score', 0)}% | Sommeil : {row.get('Whoop_Sommeil', 0)}% | VFC : {row.get('Whoop_VFC', 0)}ms")
                else:
                    st.info("Aucun check-in matinal enregistré.")
                    
            with col_hist2:
                st.subheader("🌙 Historique - Flash Soir")
                if not df_soir.empty:
                    df_s_hist = df_soir.sort_values(by='Date', ascending=False)
                    for idx, row in df_s_hist.iterrows():
                        # Récupération sécurisée peu importe le nom de la colonne dans le Sheet
                        etat = row.get('Participation du jour', row.get('Etat_Jour', 'N/C'))
                        nature = row.get('Nature de la gêne', row.get('Type_Douleur', 'N/C'))
                        zone = row.get('Localisation de la gêne', row.get('Zones_Douleur_Soir', 'Aucune'))
                        with st.expander(f"📅 {row['Date']} - Bilan : {etat}"):
                            st.markdown(f"**Type de ressenti :** {nature}")
                            st.markdown(f"**Zone(s) d'inconfort :** {zone}")
                else:
                    st.info("Aucun flash du soir enregistré.")

        # --- SOUS-ONGLET 2 : PHYSIQUE (ROMAIN) ---
        with tab_c_romain:
            st.markdown("## 🏋️‍♂️ Saisie & Suivi de la Préparation Physique (Coach)")
            
            with st.expander("➕ Enregistrer une séance de Prépa Physique"):
                with st.form("form_saisie_physique"):
                    date_seance_c = st.date_input("📅 Date de la séance", value=date.today(), key="date_sc_p")
                    col_sc1, col_sc2 = st.columns(2)
                    with col_sc1:
                        contenu_general_c = st.selectbox("🎯 Thème principal :", ["Musculation Haut", "Musculation Bas", "Cardio / Aérobie", "Vitesse / Explosivité", "Gainage / Abdos", "Prévention / Mobilité", "Récupération", "Mixte"], key="cg_p")
                    with col_sc2:
                        duree_finale_c = st.number_input("⏱️ Durée (minutes)", min_value=1, value=90, step=15, key="duree_p")
                        
                    contenu_detaille_c = st.text_area("Contenu détaillé de la séance :", height=80, key="cont_p")
                    remarques_c = st.text_area("Remarques / Observations du coach :", height=50, key="rem_p")
                    
                    note_comportement_p = st.slider("🧠 Note comportementale (1 à 10) :", min_value=1, max_value=10, value=7, key="nc_p")

                    valider_seance_physique = st.form_submit_button("🔥 Enregistrer la séance de Prépa Physique", use_container_width=True)

                if valider_seance_physique:
                    dico_p = {
                        'Date': str(date_seance_c), 
                        'Type': "Prépa Physique", 
                        'Contenu_General': contenu_general_c,
                        'Duree': duree_finale_c, 
                        'RPE': 5, 
                        'Charge': duree_finale_c * 5, 
                        'Satisfaction': 3,
                        'Whoop_Strain': 0.0, 
                        'Whoop_HR_avg': 0, 
                        'Whoop_HR_max': 0, 
                        'Whoop_Calories': 0,
                        'Contenu': contenu_detaille_c.strip(),
                        'Remarques': remarques_c.strip(),
                        'Note_Comportement': str(note_comportement_p)
                    }
                    ajouter_ligne("Seances", dico_p)
                    st.success("✅ Séance de prépa physique enregistrée avec succès !")
                    st.rerun()

            st.markdown("---")
            st.markdown("### 📜 Historique détaillé des réponses (Pôle Physique)")
            if not df_seances.empty:
                df_phys = df_seances[df_seances['Type'] == 'Prépa Physique'].copy()
                if not df_phys.empty:
                    df_phys = df_phys.sort_values(by='Date', ascending=False)
                    for index, row in df_phys.iterrows():
                        with st.expander(f"📅 {row['Date']} - {row['Contenu_General']} (Durée : {row.get('Duree', 'N/C')} min)"):
                            st.markdown(f"**Contenu détaillé :** {row.get('Contenu', 'Aucun')}")
                            st.markdown(f"**Remarques du coach :** {row.get('Remarques', 'Aucune')}")
                            st.markdown(f"**Note comportementale :** {row.get('Note_Comportement', 'N/C')} / 10")
                            st.markdown(f"**Métriques Whoop (si renseignées) :** Strain : {row.get('Whoop_Strain', 0)} | Cal : {row.get('Whoop_Calories', 0)}")
                else:
                    st.info("Aucune séance de préparation physique enregistrée pour le moment.")
            else:
                st.info("La base de données est vide.")
                
            st.markdown("---")
            st.markdown("## 📈 Saisie & Suivi des Évaluations Physiques (Tests)")
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

        # --- SOUS-ONGLET 3 : TENNIS (LUCA) ---
        with tab_c_luca:
            st.markdown("## 🎾 Saisie & Suivi des Entraînements Tennis (Coach)")
            
            with st.expander("➕ Enregistrer une séance de Tennis / Match"):
                with st.form("form_saisie_tennis"):
                    date_tennis_c = st.date_input("📅 Date de la séance", value=date.today(), key="date_sc_t")
                    col_tc1, col_tc2 = st.columns(2)
                    with col_tc1:
                        type_tennis_c = st.selectbox("🎾 Type de séance :", ["Entraînement Tennis", "Match Officiel", "Match Amical"], key="tt_t")
                        contenu_general_t = st.selectbox("🎯 Thème principal :", ["Technique", "Tactique", "Panier / Gammes", "Points dirigés", "Stratégie de Match", "Mixte"], key="cg_t")
                    with col_tc2:
                        duree_tennis_c = st.number_input("⏱️ Durée (minutes)", min_value=1, value=90, step=15, key="duree_t")
                        
                    contenu_detaille_t = st.text_area("Contenu détaillé de la séance / Match :", height=80, key="cont_t")
                    remarques_t = st.text_area("Remarques / Bilan technique ou tactique :", height=50, key="rem_t")
                    
                    note_comportement_t = st.slider("🧠 Note comportementale (1 à 10) :", min_value=1, max_value=10, value=7, key="nc_t")

                    valider_seance_tennis = st.form_submit_button("🔥 Enregistrer la séance de Tennis", use_container_width=True)

                if valider_seance_tennis:
                    dico_t = {
                        'Date': str(date_tennis_c), 
                        'Type': type_tennis_c, 
                        'Contenu_General': contenu_general_t,
                        'Duree': duree_tennis_c, 
                        'RPE': 5, 
                        'Charge': duree_tennis_c * 5, 
                        'Satisfaction': 3,
                        'Whoop_Strain': 0.0, 
                        'Whoop_HR_avg': 0, 
                        'Whoop_HR_max': 0, 
                        'Whoop_Calories': 0,
                        'Contenu': contenu_detaille_t.strip(),
                        'Remarques': remarques_t.strip(),
                        'Note_Comportement': str(note_comportement_t)
                    }
                    ajouter_ligne("Seances", dico_t)
                    st.success("✅ Séance de tennis enregistrée avec succès !")
                    st.rerun()

            st.markdown("---")
            st.markdown("### 📜 Historique détaillé des réponses (Pôle Tennis)")
            if not df_seances.empty:
                df_tennis = df_seances[df_seances['Type'].isin(['Entraînement Tennis', 'Match Officiel', 'Match Amical'])].copy()
                if not df_tennis.empty:
                    df_tennis = df_tennis.sort_values(by='Date', ascending=False)
                    for index, row in df_tennis.iterrows():
                        with st.expander(f"📅 {row['Date']} - [{row['Type']}] {row.get('Contenu_General', '')} (Durée : {row.get('Duree', 'N/C')} min)"):
                            st.markdown(f"**Contenu détaillé / Match :** {row.get('Contenu', 'Aucun')}")
                            st.markdown(f"**Remarques du coach :** {row.get('Remarques', 'Aucune')}")
                            st.markdown(f"**Note comportementale :** {row.get('Note_Comportement', 'N/C')} / 10")
                            st.markdown(f"**Ressenti / Satisfaction :** RPE {row.get('RPE', 'N/C')} | Satisfaction {row.get('Satisfaction', 'N/C')} / 5")
                else:
                    st.info("Aucune séance de tennis enregistrée pour le moment.")
            else:
                st.info("La base de données est vide.")

        # --- SOUS-ONGLET 4 : ADMIN & FRAIS ---
        with tab_c_admin:
            st.markdown("## 🚗 Registre des Frais Kilométriques (Saisie Coachs)")
            st.info("💡 Barème appliqué : 0,665 € / km. Les données s'additionnent jusqu'à ce qu'elles soient marquées comme PAYÉES.")
            
            if not df_frais.empty:
                df_frais['Distance_km'] = df_frais['Distance_km'].astype(str).str.replace(',', '.').apply(pd.to_numeric, errors='coerce').fillna(0)
                df_frais['Montant_Euros'] = df_frais['Montant_Euros'].astype(str).str.replace(',', '.').apply(pd.to_numeric, errors='coerce').fillna(0)
                if 'Coach' not in df_frais.columns:
                    df_frais['Coach'] = 'Romain'

            lieux_connus = []
            if not df_frais.empty and 'Depart' in df_frais.columns and 'Arrivee' in df_frais.columns:
                tous_lieux = pd.concat([df_frais['Depart'], df_frais['Arrivee']]).dropna().unique().tolist()
                lieux_connus = sorted([L for L in tous_lieux if L != ""])
            options_lieux = ["--- Nouveau lieu ---"] + lieux_connus

            with st.expander("➕ Saisir un nouveau déplacement (Match/Tournoi)"):
                with st.form("form_frais"):
                    date_trajet = st.date_input("📅 Date du trajet", value=date.today(), key="date_frais")
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        choix_depart = st.selectbox("📍 Départ (Choix rapide)", options_lieux, index=0)
                        saisie_depart = st.text_input("Ou saisir un nouveau départ :", disabled=(choix_depart != "--- Nouveau lieu ---"))
                    with col_f2:
                        choix_arrivee = st.selectbox("🏁 Arrivée (Choix rapide)", options_lieux, index=0)
                        saisie_arrivee = st.text_input("Ou saisir une nouvelle arrivée :", disabled=(choix_arrivee != "--- Nouveau lieu ---"))
                    
                    col_d1, col_d2, col_d3 = st.columns([1.5, 1.5, 2])
                    with col_d1:
                        distance_km = st.number_input("📏 Distance d'un aller (km)", min_value=0.0, step=1.0)
                    with col_d2:
                        coach_choisi = st.selectbox("👤 Coach responsable", ["Romain", "Luca"])
                    with col_d3:
                        st.write("")
                        st.write("")
                        aller_retour = st.checkbox("🔄 Trajet Aller-Retour (Double automatiquement la distance)")
                    
                    ajouter_frais = st.form_submit_button("💾 Ajouter à l'historique", use_container_width=True)
                    
                if ajouter_frais:
                    depart_final = saisie_depart if choix_depart == "--- Nouveau lieu ---" else choix_depart
                    arrivee_final = saisie_arrivee if choix_arrivee == "--- Nouveau lieu ---" else choix_arrivee
                    if distance_km > 0 and depart_final.strip() != "" and arrivee_final.strip() != "":
                        dist_totale = distance_km * 2 if aller_retour else distance_km
                        montant = dist_totale * 0.665
                        dico_frais = {
                            'Date': str(date_trajet),
                            'Depart': depart_final.strip(),
                            'Arrivee': arrivee_final.strip(),
                            'Distance_km': f"{dist_totale:.1f}", 
                            'Montant_Euros': f"{montant:.2f}",
                            'Statut': 'Non payé',
                            'Coach': coach_choisi
                        }
                        ajouter_ligne("Frais", dico_frais)
                        st.success(f"Déplacement attribué à {coach_choisi} enregistré en attente de paiement !")
                        st.rerun()
                    else:
                        st.error("⚠️ Veuillez remplir les lieux et indiquer une distance > 0.")
            
            st.markdown("### 🗃️ Historique Global (Tous les coachs)")
            if not df_frais.empty:
                lignes_html = ""
                for idx, row in df_frais.iterrows():
                    badge_statut = "<span style='color: #10B981; font-weight: bold;'>✅ Payé</span>" if row['Statut'] == 'Payé' else "<span style='color: #EF4444; font-weight: bold;'>⏳ En attente</span>"
                    coach_nom = row.get('Coach', 'Romain')
                    lignes_html += f"""<tr>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB;">{row['Date']}</td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB;">{row['Depart']} ➡️ {row['Arrivee']}</td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB; text-align: center;">{row['Distance_km']:.1f} km</td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB; text-align: center;"><b>{coach_nom}</b></td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB; text-align: center;">{badge_statut}</td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB; text-align: right;"><b>{row['Montant_Euros']:.2f} €</b></td>
</tr>"""

                historique_html = f"""<div style="border: 1px solid #E5E7EB; padding: 15px; border-radius: 8px; background-color: #F9FAFB; margin-bottom: 15px;">
<table style="width: 100%; font-size: 14px; border-collapse: collapse;">
<thead>
<tr style="background-color: #E5E7EB; text-transform: uppercase; font-size: 12px; color: #374151;">
<th style="padding: 8px; text-align: left;">Date</th>
<th style="padding: 8px; text-align: left;">Trajet</th>
<th style="padding: 8px; text-align: center;">Distance</th>
<th style="padding: 8px; text-align: center;">Coach</th>
<th style="padding: 8px; text-align: center;">Statut</th>
<th style="padding: 8px; text-align: right;">Montant</th>
</tr>
</thead>
<tbody>
{lignes_html}
</tbody>
</table>
</div>"""
                st.markdown(historique_html, unsafe_allow_html=True)
                
                st.markdown("### 📨 Édition de la Note de Frais par Coach")
                choix_facture_coach = st.radio("Sélectionnez le coach pour qui générer la facture :", ["Romain", "Luca"], horizontal=True)
                df_impayes_coach = df_frais[(df_frais['Statut'] != 'Payé') & (df_frais['Coach'] == choix_facture_coach)]
                
                if not df_impayes_coach.empty:
                    total_restant_coach = df_impayes_coach['Montant_Euros'].sum()
                    if st.button(f"📄 Générer la note de frais de {choix_facture_coach}", use_container_width=True):
                        lignes_impayes_html = ""
                        for idx, row in df_impayes_coach.iterrows():
                            lignes_impayes_html += f"""<tr>
<td style="padding: 10px; border-bottom: 1px solid #E5E7EB;">{row['Date']}</td>
<td style="padding: 10px; border-bottom: 1px solid #E5E7EB;">{row['Depart']} ➡️ {row['Arrivee']}</td>
<td style="padding: 10px; border-bottom: 1px solid #E5E7EB; text-align: center;">{row['Distance_km']:.1f} km</td>
<td style="padding: 10px; border-bottom: 1px solid #E5E7EB; text-align: right;"><b>{row['Montant_Euros']:.2f} €</b></td>
</tr>"""

                        facture_parents = f"""<div style="border: 2px solid #1E3A8A; padding: 30px; border-radius: 10px; background-color: #FFFFFF; margin-top: 15px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);">
<h2 style="text-align: center; color: #1E3A8A; margin-top: 0; margin-bottom: 5px;">🎾 NOTE DE FRAIS - DÉPLACEMENTS SPORTIFS</h2>
<h4 style="text-align: center; color: #374151; margin-top: 0; font-weight: normal;">Athlète : <b>Raph</b> | Accompagnateur : <b>{choix_facture_coach}</b></h4>
<p style="text-align: center; color: #6B7280; font-size: 14px; margin-top: 10px;">Document édité le : {date.today().strftime('%d/%m/%Y')} <br> Barème appliqué : 0,665 € / km</p>
<hr style="border-top: 2px solid #1E3A8A; margin: 25px 0;">
<table style="width: 100%; font-size: 15px; border-collapse: collapse; margin-bottom: 30px; color: #111827;">
<thead>
<tr style="background-color: #F3F4F6; text-transform: uppercase; font-size: 13px; color: #1E3A8A;">
<th style="padding: 12px; text-align: left;">Date</th>
<th style="padding: 12px; text-align: left;">Trajet (Aller-Retour)</th>
<th style="padding: 12px; text-align: center;">Distance</th>
<th style="padding: 12px; text-align: right;">Montant</th>
</tr>
</thead>
<tbody>
{lignes_impayes_html}
</tbody>
</table>
<div style="background-color: #1E3A8A; padding: 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
<span style="color: white; font-size: 16px;">Nombre de trajets : {len(df_impayes_coach)}</span>
<h1 style="color: white; margin: 0; font-size: 28px;">NET À PAYER : {total_restant_coach:.2f} €</h1>
</div>
<p style="text-align: center; color: #6B7280; font-size: 13px; margin-top: 20px; font-style: italic;">Merci de procéder au règlement de cette note de frais. <br><b>{choix_facture_coach}</b></p>
</div>"""
                        st.markdown(facture_parents, unsafe_allow_html=True)
                        st.balloons()
            else:
                st.info("Aucun frais kilométrique enregistré pour l'instant.")

            st.markdown("---")
            st.subheader("🌅 Base de données : Gestion & Suppression")
            
            st.markdown("**Forme (Matin)**")
            if not df_forme.empty:
                st.dataframe(df_forme, use_container_width=True)
                col_f1, col_f2 = st.columns([3, 1])
                with col_f1:
                    index_m = st.selectbox("Ligne à supprimer (Matin) :", df_forme.index)
                with col_f2:
                    if st.button("🗑️ Supprimer Forme", use_container_width=True):
                        supprimer_ligne_gsheets("Forme", index_m)
                        st.rerun()

            st.markdown("**Séances (Toutes)**")
            if not df_seances.empty:
                st.dataframe(df_seances, use_container_width=True)
                col_s1, col_s2 = st.columns([3, 1])
                with col_s1:
                    index_s = st.selectbox("Ligne à supprimer (Séance) :", df_seances.index)
                with col_s2:
                    if st.button("🗑️ Supprimer Séance", use_container_width=True):
                        supprimer_ligne_gsheets("Seances", index_s)
                        st.rerun()

            st.markdown("**Flash Soir**", unsafe_allow_html=True)
            if not df_soir.empty:
                st.dataframe(df_soir, use_container_width=True)
                col_so1, col_so2 = st.columns([3, 1])
                with col_so1:
                    index_soir = st.selectbox("Ligne à supprimer (Soir) :", df_soir.index)
                with col_so2:
                    if st.button("🗑️ Supprimer Bilan Soir", use_container_width=True):
                        supprimer_ligne_gsheets("Soir", index_soir)
                        st.rerun()

    elif saisie_mdp != "":
        st.error("❌ Mot de passe incorrect.")
