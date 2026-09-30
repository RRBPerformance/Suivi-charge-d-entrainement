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

# OPTIMISATION : Mise en cache des données
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
            # Sécurité si l'onglet Frais existait déjà sans la colonne "Statut"
            if not df_frais.empty and 'Statut' not in df_frais.columns:
                df_frais['Statut'] = "Non payé"
        except Exception:
            df_frais = pd.DataFrame(columns=['Date', 'Depart', 'Arrivee', 'Distance_km', 'Montant_Euros', 'Statut'])
            
        return df_forme, df_seances, df_soir, df_tests, df_frais
    except Exception as e:
        df_forme = pd.DataFrame(columns=['Date', 'Sommeil', 'Fatigue', 'Stress', 'Humeur', 'Score_Forme', 'Douleur_Type', 'Zones_Douleur'])
        df_seances = pd.DataFrame(columns=['Date', 'Type', 'Duree', 'RPE', 'Charge', 'Satisfaction'])
        df_soir = pd.DataFrame(columns=['Date', 'Etat_Jour', 'Zones_Douleur_Soir', 'Type_Douleur'])
        df_tests = pd.DataFrame(columns=['Date', 'Periode', 'Test', 'Cote', 'Resultat', 'Unite', 'Objectif_Prochain'])
        df_frais = pd.DataFrame(columns=['Date', 'Depart', 'Arrivee', 'Distance_km', 'Montant_Euros', 'Statut'])
        return df_forme, df_seances, df_soir, df_tests, df_frais

def ajouter_ligne(onglet_nom, dico_donnees):
    try:
        sh = init_connection()
        try:
            worksheet = sh.worksheet(onglet_nom)
        except Exception:
            worksheet = sh.add_worksheet(title=onglet_nom, rows="100", cols="20")
            
        if len(worksheet.get_all_values()) == 0:
            worksheet.append_row(list(dico_donnees.keys()))
            
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

def marquer_paye_gsheets(onglet_nom, index_ligne):
    try:
        sh = init_connection()
        worksheet = sh.worksheet(onglet_nom)
        # Met à jour la ligne avec "Payé" dans la 6ème colonne (Statut)
        worksheet.update_cell(index_ligne + 2, 6, "Payé")
        # Sécurité : force l'en-tête de la colonne 6 à "Statut" au cas où
        worksheet.update_cell(1, 6, "Statut")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur lors du passage en Payé : {e}")

# Titre principal
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

# --- ONGLET 1 : MATIN ---
with tab_matin:
    st.info("💡 **Consigne :** À remplir chaque matin au réveil pour adapter la charge de la journée.")
    
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

# --- ONGLET 2 : SÉANCES ---
with tab_seance:
    st.info("⏱ **Rappel :** À remplir dans les 30 minutes suivant la fin de l'effort.")
    
    date_seance = st.date_input("📅 Date de la séance", value=date.today(), key="date_s")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        type_final = st.selectbox("🎾 Type de séance", ["Prépa Physique", "Tennis", "Récupération", "Match"])
    with col_m2:
        duree_finale = st.number_input("⏱️ Durée (minutes)", min_value=1, value=90, step=15)
        
    st.markdown("### 📡 1. Données de la Montre (Saisie Manuelle)")
    st.caption("Recopie les données de ta séance depuis l'application WHOOP (laisse à 0 si pas de montre).")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        whoop_strain = st.number_input("🔥 Strain (Effort 0-21)", min_value=0.0, max_value=21.0, value=0.0, step=0.1)
        whoop_cal = st.number_input("⚡ Énergie (kcal)", min_value=0, value=0)
    with col_w2:
        whoop_hr_avg = st.number_input("💓 FC Moyenne (bpm)", min_value=0, value=0)
        whoop_hr_max = st.number_input("🚨 FC Max (bpm)", min_value=0, value=0)
        
    st.markdown("---")
    st.markdown("### 🧠 2. Ton Ressenti (Subjectif)")

    col3, col4 = st.columns(2)
    with col3:
        rpe = st.slider("🥵 Difficulté ressentie (RPE 1-10)", 1, 10, 5)
    with col4:
        satisfaction = st.slider("🎯 Satisfaction technique/tactique (1-5)", 1, 5, 3)
        
    st.markdown("#### ⚡ Analyse de la charge")
    charge = duree_finale * rpe
    
    if whoop_strain > 0:
        strain_sur_10 = (whoop_strain / 21) * 10
        ecart = rpe - strain_sur_10
        
        if ecart >= 3:
            st.warning("⚠️ **Alerte Fatigue Nerveuse :** Tu as ressenti cette séance comme très dure par rapport à l'impact cardio. Signe possible d'une fatigue neuromusculaire.")
        elif ecart <= -3:
            st.warning("⚠️ **Alerte Surcharge :** La séance t'a paru facile, mais ton organisme a pris un gros impact cardio (Strain élevé).")
        else:
            st.success("✅ **Cohérence parfaite :** Ton ressenti correspond à la dépense mesurée.")

    if st.button("🔥 Enregistrer la séance", use_container_width=True):
        dico = {
            'Date': str(date_seance), 
            'Type': type_final, 
            'Duree': duree_finale, 
            'RPE': rpe, 
            'Charge': charge, 
            'Satisfaction': satisfaction,
            'Whoop_Strain': whoop_strain, 
            'Whoop_HR_avg': whoop_hr_avg, 
            'Whoop_HR_max': whoop_hr_max, 
            'Whoop_Calories': whoop_cal
        }
        ajouter_ligne("Seances", dico)
        st.success(f"📊 Séance validée ! Charge : {charge} unités.")

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
        
        st.markdown("---")
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
        st.markdown("## 📈 Tableaux de Bord")
        
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
                    df_pivot.index = df_pivot.index.strftime('%Y-%m-%d')
                    st.bar_chart(df_pivot)
                else:
                    df_jour = df_s.groupby('Date')['Charge'].sum().reset_index().set_index('Date').sort_index()
                    df_glissant = df_jour.rolling(window='7D', min_periods=1).sum()
                    df_glissant.index = df_glissant.index.strftime('%Y-%m-%d')
                    st.line_chart(df_glissant)
            else:
                st.info("Pas assez de données.")

        st.markdown("---")
        st.subheader("🌅 Gérer les Bases de Données (Suppression)")
        
        col_db1, col_db2, col_db3 = st.columns(3)
        with col_db1:
            if not df_forme.empty:
                index_m = st.selectbox("Ligne (Matin) :", df_forme.index)
                if st.button("🗑️ Supprimer Forme"):
                    supprimer_ligne_gsheets("Forme", index_m)
                    st.rerun()
        with col_db2:
            if not df_seances.empty:
                index_s = st.selectbox("Ligne (Séance) :", df_seances.index)
                if st.button("🗑️ Supprimer Séance"):
                    supprimer_ligne_gsheets("Seances", index_s)
                    st.rerun()
        with col_db3:
            if not df_soir.empty:
                index_soir = st.selectbox("Ligne (Soir) :", df_soir.index)
                if st.button("🗑️ Supprimer Bilan Soir"):
                    supprimer_ligne_gsheets("Soir", index_soir)
                    st.rerun()

        # ==========================================
        # --- NOUVELLE SECTION : GESTION DES FRAIS AVEC STATUT ---
        # ==========================================
        st.markdown("---")
        st.markdown("## 🚗 Registre des Frais Kilométriques")
        st.info("💡 Barème appliqué : 0,665 € / km. Tous les trajets s'additionnent jusqu'à ce qu'ils soient marqués comme PAYÉS.")
        
        with st.expander("➕ Saisir un nouveau déplacement (Match/Tournoi)"):
            with st.form("form_frais"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    date_trajet = st.date_input("📅 Date du trajet", value=date.today(), key="date_frais")
                    depart = st.text_input("📍 Lieu de départ (ex: Guéthary)")
                with col_f2:
                    distance_km = st.number_input("📏 Distance (km)", min_value=0.0, step=1.0)
                    arrivee = st.text_input("🏁 Lieu d'arrivée (ex: Anglet)")
                
                ajouter_frais = st.form_submit_button("💾 Ajouter à la note de frais", use_container_width=True)
                
            if ajouter_frais:
                if distance_km > 0 and depart != "" and arrivee != "":
                    montant = distance_km * 0.665
                    dico_frais = {
                        'Date': str(date_trajet),
                        'Depart': depart,
                        'Arrivee': arrivee,
                        'Distance_km': distance_km,
                        'Montant_Euros': round(montant, 2),
                        'Statut': 'Non payé' # Le trajet naît "Non payé" par défaut
                    }
                    ajouter_ligne("Frais", dico_frais)
                    st.success("Déplacement enregistré en attente de paiement !")
                    st.rerun()
                else:
                    st.error("⚠️ Veuillez remplir les lieux et indiquer une distance > 0.")
        
        # --- GÉNÉRATION DE LA FACTURE INTELLIGENTE ---
        st.markdown("### 🧾 Note de Frais Globale")
        if not df_frais.empty:
            # Sécurisation des types
            df_frais['Distance_km'] = pd.to_numeric(df_frais['Distance_km'], errors='coerce').fillna(0)
            df_frais['Montant_Euros'] = pd.to_numeric(df_frais['Montant_Euros'], errors='coerce').fillna(0)
            
            # Calcul des totaux séparés (Payé vs Non Payé)
            total_restant = df_frais[df_frais['Statut'] != 'Payé']['Montant_Euros'].sum()
            total_paye = df_frais[df_frais['Statut'] == 'Payé']['Montant_Euros'].sum()
            
            # Construction des lignes HTML
            lignes_html = ""
            for idx, row in df_frais.iterrows():
                # On met un badge vert ou rouge selon le statut
                badge_statut = "<span style='color: #10B981; font-weight: bold;'>✅ Payé</span>" if row['Statut'] == 'Payé' else "<span style='color: #EF4444; font-weight: bold;'>⏳ En attente</span>"
                
                lignes_html += f"""<tr>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB;">{row['Date']}</td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB;">{row['Depart']} ➡️ {row['Arrivee']}</td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB; text-align: center;">{row['Distance_km']:.1f} km</td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB; text-align: center;">{badge_statut}</td>
<td style="padding: 10px; border-bottom: 1px solid #D1D5DB; text-align: right;"><b>{row['Montant_Euros']:.2f} €</b></td>
</tr>"""

            facture_html = f"""<div style="border: 2px solid #1E3A8A; padding: 25px; border-radius: 10px; background-color: #F3F4F6; margin-top: 15px;">
<h2 style="text-align: center; color: #1E3A8A; margin-top: 0; margin-bottom: 5px;">🎾 RÉCAPITULATIF DES FRAIS DE DÉPLACEMENT</h2>
<p style="text-align: center; color: #6B7280; font-size: 14px; margin-top: 0;">Généré le {date.today().strftime('%d/%m/%Y')}</p>
<hr style="border-top: 2px dashed #9CA3AF; margin: 20px 0;">
<table style="width: 100%; font-size: 15px; border-collapse: collapse; margin-bottom: 25px;">
<thead>
<tr style="background-color: #E5E7EB; text-transform: uppercase; font-size: 13px; color: #374151;">
<th style="padding: 10px; text-align: left;">Date</th>
<th style="padding: 10px; text-align: left;">Trajet</th>
<th style="padding: 10px; text-align: center;">Distance</th>
<th style="padding: 10px; text-align: center;">Statut</th>
<th style="padding: 10px; text-align: right;">Montant</th>
</tr>
</thead>
<tbody>
{lignes_html}
</tbody>
</table>
<div style="background-color: #10B981; padding: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
<span style="color: white; font-size: 16px;">Déjà remboursé : {total_paye:.2f} €</span>
<h1 style="color: white; margin: 0; font-size: 26px;">RESTE À PAYER : {total_restant:.2f} €</h1>
</div>
</div>"""
            st.markdown(facture_html, unsafe_allow_html=True)
            
            # --- ACTIONS : MARQUER PAYÉ OU SUPPRIMER ---
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("💳 Gérer les paiements ou Supprimer un trajet"):
                st.dataframe(df_frais, use_container_width=True)
                
                col_act1, col_act2, col_act3 = st.columns([2, 1, 1])
                with col_act1:
                    index_action = st.selectbox("Sélectionner la ligne concernée :", df_frais.index, key="action_frais")
                with col_act2:
                    st.write("")
                    st.write("")
                    if st.button("✅ Marquer PAYÉ", use_container_width=True):
                        marquer_paye_gsheets("Frais", index_action)
                        st.success("Le trajet a bien été marqué comme payé !")
                        st.rerun()
                with col_act3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ Supprimer", use_container_width=True):
                        supprimer_ligne_gsheets("Frais", index_action)
                        st.success("Déplacement supprimé de l'historique.")
                        st.rerun()
        else:
            st.info("Aucun frais kilométrique enregistré pour l'instant.")

    elif saisie_mdp != "":
        st.error("❌ Mot de passe incorrect.")
