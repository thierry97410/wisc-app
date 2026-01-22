import streamlit as st
import google.generativeai as genai
import os
import io
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO
from pypdf import PdfReader
from docx import Document
from datetime import date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant WISC-V", page_icon="🧠", layout="wide")
st.title("🧠 Assistant d'Analyse Expert en WISC V")

# --- AVERTISSEMENT ---
st.warning("⚠️ **AVERTISSEMENT :** Outil d'aide à la rédaction. L'analyse clinique reste la responsabilité du psychologue.")

# --- CONNEXION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante dans les secrets Streamlit.")
    st.stop()

# --- FONCTIONS UTILITAIRES ---
def calculer_age(d_naiss, d_bilan):
    try:
        if d_bilan < d_naiss: return 0, 0
        ans = d_bilan.year - d_naiss.year
        mois = d_bilan.month - d_naiss.month
        if d_bilan.day < d_naiss.day: mois -= 1
        if mois < 0: ans -= 1; mois += 12
        return ans, mois
    except: return 0, 0

def check_homogeneite_indice(val1, val2, nom_indice):
    if val1 == 0 or val2 == 0: return None, ""
    ecart = abs(val1 - val2)
    if ecart >= 5: return False, f"⚠️ {nom_indice} Hétérogène (Écart {ecart})"
    else: return True, f"✅ {nom_indice} Homogène"

def plot_radar_chart(indices_dict):
    labels = list(indices_dict.keys())
    values = list(indices_dict.values())
    if sum(values) == 0: return None
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='#1f77b4', alpha=0.25)
    ax.plot(angles, values, color='#1f77b4', linewidth=2, label='Enfant')
    ax.plot(np.linspace(0, 2*np.pi, 100), [100]*100, color='red', linestyle='--', linewidth=1, label='Norme (100)')
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(40, 160)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize='small')
    return fig

def read_file(file_obj, filename):
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            pdf_reader = PdfReader(file_obj)
            for page in pdf_reader.pages:
                t = page.extract_text()
                if t: text += t + "\n"
        else:
            if isinstance(file_obj, str): 
                with open(file_obj, "r", encoding="utf-8") as f: text = f.read()
            else: 
                stringio = StringIO(file_obj.getvalue().decode("utf-8"))
                text = stringio.read()
    except: pass
    return text

def create_docx(text_content, prenom, age_str):
    doc = Document()
    doc.add_heading(f'Compte Rendu WISC-V : {prenom}', 0)
    doc.add_paragraph(f"Âge au bilan : {age_str}")
    p = doc.add_paragraph()
    runner = p.add_run("AVERTISSEMENT : Ce document est une base de travail. L'analyse clinique relève de la responsabilité du psychologue signataire.")
    runner.bold = True; runner.italic = True
    doc.add_paragraph(text_content)
    bio = io.BytesIO()
    doc.save(bio)
    return bio

# --- SIDEBAR (CHARGEMENT AUTO) ---
knowledge_base = ""
with st.sidebar:
    st.header("📚 Bibliothèque (Auto)")
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    if local_files:
        with st.spinner("Chargement des sources..."):
            for f in local_files:
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
        st.success(f"✅ {len(local_files)} documents actifs")
        with st.expander("Voir détails"):
            for f in local_files: st.caption(f"📄 {f}")
    else:
        st.warning("Aucun document PDF trouvé.")

# ==========================================
# 1. IDENTITÉ
# ==========================================
st.header("1. Identité")
col_id1, col_id2, col_id3 = st.columns(3)

with col_id1:
    st.markdown("##### 👤 L'Enfant")
    prenom = st.text_input("Prénom", placeholder="Ex: Lucas")
    sexe = st.radio("Sexe", ["Garçon", "Fille"], horizontal=True)
    lateralite = st.radio("Latéralité", ["Droitier", "Gaucher"], horizontal=True)

with col_id2:
    st.markdown("##### 🎂 Naissance")
    cn_j, cn_m, cn_a = st.columns([1, 1, 1.5])
    with cn_j: j_n = st.number_input("J", 1, 31, 1, key="jn")
    with cn_m: m_n = st.number_input("M", 1, 12, 1, key="mn")
    with cn_a: a_n = st.number_input("A", 2000, 2030, 2015, key="an")
    try: d_naiss = date(a_n, m_n, j_n)
    except: d_naiss = date.today()

with col_id3:
    st.markdown("##### 📅 Bilan")
    cb_j, cb_m, cb_a = st.columns([1, 1, 1.5])
    with cb_j: j_b = st.number_input("J", 1, 31, date.today().day, key="jb")
    with cb_m: m_b = st.number_input("M", 1, 12, date.today().month, key="mb")
    with cb_a: a_b = st.number_input("A", 2020, 2030, date.today().year, key="ab")
    try: d_test = date(a_b, m_b, j_b)
    except: d_test = date.today()
    ans, mois = calculer_age(d_naiss, d_test)
    st.success(f"Âge : **{ans} ans et {mois} mois**")

st.markdown("---")

# ==========================================
# 2. ANAMNÈSE ET OBSERVATIONS
# ==========================================
st.header("2. Anamnèse et Observations")
col_check1, col_check2, col_check3 = st.columns(3)
obs_cliniques = []

with col_check1:
    st.markdown("**Attitude**")
    if st.checkbox("Anxiété de performance"): obs_cliniques.append("Anxiété de performance")
    if st.checkbox("Opposition / Retrait"): obs_cliniques.append("Opposition ou retrait")
    if st.checkbox("Agitation"): obs_cliniques.append("Agitation motrice")
    if st.checkbox("Impulsivité"): obs_cliniques.append("Impulsivité")

with col_check2:
    st.markdown("**Cognition & Communication**")
    if st.checkbox("Fatigabilité"): obs_cliniques.append("Fatigabilité rapide")
    if st.checkbox("Défaut d'attention"): obs_cliniques.append("Défaut d'attention")
    if st.checkbox("Besoin de relance"): obs_cliniques.append("Besoin de relance")
    st.markdown("---")
    if st.checkbox("Verbalisation +++ (Abondante)"): obs_cliniques.append("Verbalisation abondante/Logorrhée")
    if st.checkbox("Verbalisation --- (Pauvre/Mutisme)"): obs_cliniques.append("Verbalisation pauvre, voire mutisme")

with col_check3:
    st.markdown("**Graphisme**")
    if st.checkbox("Crispation"): obs_cliniques.append("Crispation graphique")
    if st.checkbox("Lenteur"): obs_cliniques.append("Lenteur graphique")
    if st.checkbox("Autocritique"): obs_cliniques.append("Autocritique excessive")
    st.markdown("---")
    st.markdown("🗣️ **Langue / Créole**")
    creole = st.radio("Usage du Créole", ["-- (Non/Peu)", "+- (Moyen)", "++ (Dominant)"], index=0, label_visibility="collapsed")

ana = st.text_area("Anamnèse", height=80, placeholder="Contexte familial, motif, scolarité...")
obs_libre = st.text_area("Autres observations", height=80)

st.markdown("---")

# ==========================================
# 3. PSYCHOMÉTRIE
# ==========================================
st.header("3. Psychométrie")

st.subheader("A. Profil des Notes Standards")

# Ligne 1
c1, c2, c3, c4 = st.columns(4)
with c1: sim = st.number_input("Similitudes (SIM)", 0, 19, 0)
with c2: voc = st.number_input("Vocabulaire (VOC)", 0, 19, 0)
with c3: info = st.number_input("Information (INF)", 0, 19, 0)
with c4: comp = st.number_input("Compréhension (COM)", 0, 19, 0)
# Ligne 2
c1, c2 = st.columns(2)
with c1: cub = st.number_input("Cubes (CUB)", 0, 19, 0)
with c2: puz = st.number_input("Puzzles (PUZ)", 0, 19, 0)
# Ligne 3
c1, c2, c3 = st.columns(3)
with c1: mat = st.number_input("Matrices (MAT)", 0, 19, 0)
with c2: bal = st.number_input("Balances (BAL)", 0, 19, 0)
with c3: arit = st.number_input("Arithmétique (ARI)", 0, 19, 0)
# Ligne 4
c1, c2, c3 = st.columns(3)
with c1: memc = st.number_input("Mém. Chiffres (MCH)", 0, 19, 0)
with c2: memi = st.number_input("Mém. Images (MIM)", 0, 19, 0)
with c3: seq = st.number_input("Séquence L-C (SLC)", 0, 19, 0)
# Ligne 5
c1, c2, c3 = st.columns(3)
with c1: cod = st.number_input("Code (COD)", 0, 19, 0)
with c2: sym = st.number_input("Symboles (SYM)", 0, 19, 0)
with c3: bar = st.number_input("Barrage (BAR)", 0, 19, 0)

st.markdown("---")

st.subheader("B. Profil des Notes Composites & Percentiles")

somme_iag = sim + voc + cub + mat + bal
somme_icc = memc + memi + sym + cod
somme_inv = cub + puz + mat + bal + memi + cod

# Vérif Homogénéité Subtests (Grégoire)
valid_icv, txt_icv = check_homogeneite_indice(sim, voc, "ICV")
valid_ivs, txt_ivs = check_homogeneite_indice(cub, puz, "IVS")
valid_irf, txt_irf = check_homogeneite_indice(mat, bal, "IRF")
valid_imt, txt_imt = check_homogeneite_indice(memc, memi, "IMT")
valid_ivt, txt_ivt = check_homogeneite_indice(sym, cod, "IVT")

etats_indices = [txt_icv, txt_ivs, txt_irf, txt_imt, txt_ivt]
nb_indices_invalides = sum([1 for x in [valid_icv, valid_ivs, valid_irf, valid_imt, valid_ivt] if x is False])

# QIT - Layout
col_qit1, col_qit2, col_qit3, col_qit4, col_qit5 = st.columns(5)
with col_qit1: qit = st.number_input("QIT (Total)", 0, 160, 0)
with col_qit2: perc_qit = st.number_input("Perc. QIT", 0.0, 100.0, 0.0)
with col_qit3: qit_bas = st.number_input("IC Bas QIT", 0, 160, 0)
with col_qit4: qit_haut = st.number_input("IC Haut QIT", 0, 160, 0)
# col_qit5 est réservé pour l'affichage APRES la définition des indices

# Indices Principaux (5 colonnes)
c1, c2, c3, c4, c5 = st.columns(5)

# ICV
with c1: 
    st.markdown("**ICV**")
    icv = st.number_input("Score ICV", 0, 160, 0, label_visibility="collapsed")
    perc_icv = st.number_input("Perc ICV", 0.0, 100.0, 0.0, label_visibility="collapsed")
    st.caption("Intervalle Confiance")
    icv_bas = st.number_input("ICV Bas", 0, 160, 0, label_visibility="collapsed")
    icv_haut = st.number_input("ICV Haut", 0, 160, 0, label_visibility="collapsed")
    if txt_icv: st.caption(txt_icv)

# IVS
with c2: 
    st.markdown("**IVS**")
    ivs = st.number_input("Score IVS", 0, 160, 0, label_visibility="collapsed")
    perc_ivs = st.number_input("Perc IVS", 0.0, 100.0, 0.0, label_visibility="collapsed")
    st.caption("Intervalle Confiance")
    ivs_bas = st.number_input("IVS Bas", 0, 160, 0, label_visibility="collapsed")
    ivs_haut = st.number_input("IVS Haut", 0, 160, 0, label_visibility="collapsed")
    if txt_ivs: st.caption(txt_ivs)

# IRF
with c3: 
    st.markdown("**IRF**")
    irf = st.number_input("Score IRF", 0, 160, 0, label_visibility="collapsed")
    perc_irf = st.number_input("Perc IRF", 0.0, 100.0, 0.0, label_visibility="collapsed")
    st.caption("Intervalle Confiance")
    irf_bas = st.number_input("IRF Bas", 0, 160, 0, label_visibility="collapsed")
    irf_haut = st.number_input("IRF Haut", 0, 160, 0, label_visibility="collapsed")
    if txt_irf: st.caption(txt_irf)

# IMT
with c4: 
    st.markdown("**IMT**")
    imt = st.number_input("Score IMT", 0, 160, 0, label_visibility="collapsed")
    perc_imt = st.number_input("Perc IMT", 0.0, 100.0, 0.0, label_visibility="collapsed")
    st.caption("Intervalle Confiance")
    imt_bas = st.number_input("IMT Bas", 0, 160, 0, label_visibility="collapsed")
    imt_haut = st.number_input("IMT Haut", 0, 160, 0, label_visibility="collapsed")
    if txt_imt: st.caption(txt_imt)

# IVT
with c5: 
    st.markdown("**IVT**")
    ivt = st.number_input("Score IVT", 0, 160, 0, label_visibility="collapsed")
    perc_ivt = st.number_input("Perc IVT", 0.0, 100.0, 0.0, label_visibility="collapsed")
    st.caption("Intervalle Confiance")
    ivt_bas = st.number_input("IVT Bas", 0, 160, 0, label_visibility="collapsed")
    ivt_haut = st.number_input("IVT Haut", 0, 160, 0, label_visibility="collapsed")
    if txt_ivt: st.caption(txt_ivt)

# --- CALCUL VALIDITÉ QIT (MAINTENANT QUE LES VARIABLES EXISTENT) ---
with col_qit5:
    indices_check = [icv, ivs, irf, imt, ivt]
    if all(i > 0 for i in indices_check):
        ecart_max = max(indices_check) - min(indices_check)
        if ecart_max >= 23:
            st.error(f"🔴 **Invalide** (Disp. {ecart_max})")
            homogeneite_txt = f"QIT NON INTERPRÉTABLE (Hétérogène, dispersion {ecart_max})"
        elif nb_indices_invalides >= 2:
            st.warning(f"🟠 **Fragile**")
            homogeneite_txt = f"QIT FRAGILE ({nb_indices_invalides} indices hétérogènes)"
        else:
            st.success(f"✅ **Homogène**")
            homogeneite_txt = "QIT Valide et Homogène"
    else:
        st.info("Calcul Homogénéité..."); homogeneite_txt = "Non calculé"

st.markdown("---")

# Complémentaires
st.caption(f"Calculs : IAG ({somme_iag}) | ICC ({somme_icc}) | INV ({somme_inv})")
c1, c2, c3 = st.columns(3)
with c1: 
    st.markdown("**IAG**")
    iag = st.number_input("Score IAG", 0, 160, 0, label_visibility="collapsed")
    iag_bas = st.number_input("IAG Bas", 0, 160, 0, label_visibility="collapsed")
    iag_haut = st.number_input("IAG Haut", 0, 160, 0, label_visibility="collapsed")
with c2: 
    st.markdown("**ICC**")
    icc = st.number_input("Score ICC", 0, 160, 0, label_visibility="collapsed")
    icc_bas = st.number_input("ICC Bas", 0, 160, 0, label_visibility="collapsed")
    icc_haut = st.number_input("ICC Haut", 0, 160, 0, label_visibility="collapsed")
with c3: 
    st.markdown("**INV**")
    inv = st.number_input("Score INV", 0, 160, 0, label_visibility="collapsed")
    inv_bas = st.number_input("INV Bas", 0, 160, 0, label_visibility="collapsed")
    inv_haut = st.number_input("INV Haut", 0, 160, 0, label_visibility="collapsed")

# --- STATS & GRAPH ---
st.divider()
col_graph, col_stats = st.columns([1, 1.5])
indices_principaux = {"ICV": icv, "IVS": ivs, "IRF": irf, "IMT": imt, "IVT": ivt}
indices_valides = {k: v for k, v in indices_principaux.items() if v > 0}

with col_graph:
    st.subheader("📊 Profil vs Norme")
    if len(indices_valides) >= 3:
        fig = plot_radar_chart(indices_valides)
        if fig: st.pyplot(fig)

with col_stats:
    st.subheader("📈 Analyse Intra-individuelle")
    if len(indices_valides) > 0:
        valeurs = list(indices_valides.values())
        moyenne_perso = np.mean(valeurs)
        ecart_type_perso = np.std(valeurs)
        
        st.info(f"**Moyenne Personnelle : {moyenne_perso:.1f}**\n**Écart-Type Personnel : {ecart_type_perso:.1f}**\n*(Mesure de la dispersion interne)*")
        
        txt_stats = f"Moyenne Perso: {moyenne_perso:.1f}, Ecart-Type Perso: {ecart_type_perso:.1f}."
        for k, v in indices_valides.items():
            diff = v - moyenne_perso
            if diff >= 10:
                st.write(f"🟢 **{k} ({v})** : Force Relative (+{diff:.1f})")
                txt_stats += f"- {k} ({v}): Force Relative (>{moyenne_perso:.1f}). "
            elif diff <= -10:
                st.write(f"🔴 **{k} ({v})** : Faiblesse Relative ({diff:.1f})")
                txt_stats += f"- {k} ({v}): Faiblesse Relative (<{moyenne_perso:.1f}). "
            else:
                 st.caption(f"⚪ {k} ({v}) : Zone Moyenne Personnelle")
    else: txt_stats = ""

# --- GENERATION ---
st.markdown("---")
if st.button(f"✨ Lancer l'Analyse Expert", type="primary"):
    
    infos = f"Enfant: {prenom}, {sexe}. Age: {ans} ans {mois} mois. Latéralité: {lateralite}."
    contexte_langue = f"Utilisation du Créole : {creole}"
    observations_compilees = ", ".join(obs_cliniques) + ". " + obs_libre
    
    infos_validite = f"VALIDITÉ QIT : {homogeneite_txt}.\nVALIDITÉ INDICES (Grégoire >= 5) :\n"
    for etat in etats_indices:
        if etat: infos_validite += f"- {etat}\n"

    # Construction des Scores COMPLETS avec IC
    data = f"{infos_validite}\nSCORES PRINCIPAUX:\n"
    if qit > 0: 
        data += f"- QIT (Total): {qit} (Percentile: {perc_qit}). Intervalle de Confiance (95%): {qit_bas}-{qit_haut}\n"
    
    data += "\nINDICES (Note / Percentile / IC 95%):\n"
    if icv > 0: data += f"- ICV: {icv} (Perc: {perc_icv}, IC: {icv_bas}-{icv_haut})\n"
    if ivs > 0: data += f"- IVS: {ivs} (Perc: {perc_ivs}, IC: {ivs_bas}-{ivs_haut})\n"
    if irf > 0: data += f"- IRF: {irf} (Perc: {perc_irf}, IC: {irf_bas}-{irf_haut})\n"
    if imt > 0: data += f"- IMT: {imt} (Perc: {perc_imt}, IC: {imt_bas}-{imt_haut})\n"
    if ivt > 0: data += f"- IVT: {ivt} (Perc: {perc_ivt}, IC: {ivt_bas}-{ivt_haut})\n"

    data += "\nINDICES COMPLÉMENTAIRES (Note / IC 95%):\n"
    if iag > 0: data += f"- IAG: {iag} (IC: {iag_bas}-{iag_haut})\n"
    if icc > 0: data += f"- ICC: {icc} (IC: {icc_bas}-{icc_haut})\n"
    if inv > 0: data += f"- INV: {inv} (IC: {inv_bas}-{inv_haut})\n"

    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    data += "\nSUBTESTS:\n"
    for k,v in sub_map.items():
        if v > 0: data += f"- {k}: {v}\n"

    with st.spinner(f"Rédaction de l'analyse expert (IC 95%)..."):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Rôle: Expert Psychologue WISC-V (Contexte La Réunion).
            AVERTISSEMENT: Outil d'aide, analyse à vérifier par le psy.
            
            CONTEXTE PSYCHOMÉTRIQUE:
            - **Rigueur Statistique**: Utilise systématiquement les **Intervalles de Confiance (IC 95%)** fournis pour nuancer les scores.
            - Exemple de formulation attendue: "Le QIT est de 100 (rang percentile 50). Il y a 95% de chances que son vrai niveau se situe dans l'intervalle compris entre [Bas] et [Haut]."
            
            CONTEXTE ENFANT: {infos}
            LANGUE: {contexte_langue}.
            OBSERVATIONS: {observations_compilees}
            ANAMNÈSE: {ana}
            
            RÉSULTATS & VALIDITÉ:
            {data}
            
            STATISTIQUES INTRA-INDIVIDUELLES (IPSATIVE):
            - Moyenne Personnelle : {moyenne_perso if len(indices_valides)>0 else 'N/A'}
            - Écart-Type Personnel : {ecart_type_perso if len(indices_valides)>0 else 'N/A'}
            - Détail Forces/Faiblesses : {txt_stats}
            
            SOURCES: {knowledge_base}
            
            CONSIGNE DE RÉDACTION STRICTE:
            1. INTRODUCTION & VALIDITÉ :
               - Analyse QIT + Homogénéité.
               - Mentionne l'intervalle de confiance du QIT dès l'intro.
            
            2. ANALYSE INTER-INDIVIDUELLE (NORMATIVE) :
               - Pour chaque indice, cite la note, le percentile ET l'intervalle de confiance.
            
            3. ANALYSE INTRA-INDIVIDUELLE (PERSONNELLE) :
               - Compare à la MOYENNE PERSONNELLE ({moyenne_perso if len(indices_valides)>0 else 'N/A'}).
               - Utilise l'écart-type personnel.
            
            4. RECOMMANDATIONS.
            """
            
            res = model.generate_content(prompt)
            st.markdown("### Résultat :")
            st.markdown(res.text)
            
            filename = f"Bilan_{prenom}_{ans}ans.docx" if prenom else "Bilan.docx"
            docx_file = create_docx(res.text, prenom, f"{ans} ans {mois} mois")
            st.download_button("📄 Télécharger Word", docx_file, filename, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
        except Exception as e: st.error(f"Erreur : {e}")
