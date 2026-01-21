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

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Cockpit", page_icon="🚀", layout="wide")
st.title("🧠 Assistant WISC-V : Cockpit Complet")

# --- CONNEXION ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- FONCTION CALCUL AGE ---
def calculer_age(d_naiss, d_bilan):
    try:
        if d_bilan < d_naiss: return 0, 0
        ans = d_bilan.year - d_naiss.year
        mois = d_bilan.month - d_naiss.month
        if d_bilan.day < d_naiss.day: mois -= 1
        if mois < 0:
            ans -= 1
            mois += 12
        return ans, mois
    except:
        return 0, 0

# --- FONCTION GRAPHIQUE RADAR ---
def plot_radar_chart(indices_dict):
    # Filtrer les valeurs > 0
    labels = list(indices_dict.keys())
    values = list(indices_dict.values())
    
    # Si pas de données, on ne dessine rien
    if sum(values) == 0: return None

    # Fermeture du cercle pour le graphique
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='blue', alpha=0.25)
    ax.plot(angles, values, color='blue', linewidth=2)
    
    # Labels
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    
    # Echelle fixe pour comparabilité (40 à 160)
    ax.set_ylim(40, 160)
    ax.grid(True, color='grey', linestyle='--', alpha=0.5)
    
    return fig

# --- FONCTION LECTURE ---
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

# --- EXPORT WORD ---
def create_docx(text_content, prenom, age_str):
    doc = Document()
    doc.add_heading(f'Compte Rendu WISC-V : {prenom}', 0)
    doc.add_paragraph(f"Âge au bilan : {age_str}")
    doc.add_paragraph(text_content)
    bio = io.BytesIO()
    doc.save(bio)
    return bio

# --- SIDEBAR ---
knowledge_base = ""
total_chars = 0
LIMIT_CHARS = 800000

with st.sidebar:
    st.header("📚 Bibliothèque")
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    if local_files:
        for f in local_files:
            if st.checkbox(f"📄 {f}", value=False):
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
                total_chars += len(c)
    st.divider()
    if total_chars > LIMIT_CHARS: st.error("🛑 Trop lourd !")
    elif total_chars > 0: st.success("✅ Poids OK")

# --- INTERFACE ---
st.subheader("1. Identité & Chronologie")
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

st.divider()

# --- PARTIE SCORES ---
col_scores, col_inputs = st.columns([1, 1])

with col_scores:
    st.subheader("2. Subtests (Notes Standard)")
    sc1, sc2 = st.columns(2)
    with sc1:
        sim = st.number_input("Similitudes", 0, 19, 0)
        voc = st.number_input("Vocabulaire", 0, 19, 0)
        cub = st.number_input("Cubes", 0, 19, 0)
        mat = st.number_input("Matrices", 0, 19, 0)
        bal = st.number_input("Balances", 0, 19, 0)
        arit = st.number_input("Arithmétique", 0, 19, 0)
        cod = st.number_input("Code", 0, 19, 0)
    with sc2:
        info = st.number_input("Information", 0, 19, 0)
        comp = st.number_input("Compréhension", 0, 19, 0)
        puz = st.number_input("Puzzles", 0, 19, 0)
        memc = st.number_input("Mém. Chiffres", 0, 19, 0)
        memi = st.number_input("Mém. Images", 0, 19, 0)
        sym = st.number_input("Symboles", 0, 19, 0)
        seq = st.number_input("Séquence", 0, 19, 0)
        bar = st.number_input("Barrage", 0, 19, 0)

with col_inputs:
    st.subheader("3. Indices & Analyse")
    
    # Aides Calcul
    somme_iag = sim + voc + cub + mat + bal
    somme_icc = memc + memi + sym + cod
    somme_inv = cub + puz + mat + bal + memi + cod
    st.caption(f"Aide : IAG={somme_iag} | ICC={somme_icc} | INV={somme_inv}")
    
    ic1, ic2 = st.columns(2)
    with ic1:
        qit = st.number_input("QIT", 0, 160, 0)
        icv = st.number_input("ICV", 0, 160, 0)
        ivs = st.number_input("IVS", 0, 160, 0)
        irf = st.number_input("IRF", 0, 160, 0)
    with ic2:
        imt = st.number_input("IMT", 0, 160, 0)
        ivt = st.number_input("IVT", 0, 160, 0)
        iag = st.number_input("IAG", 0, 160, 0)
        icc = st.number_input("ICC", 0, 160, 0)
        inv = st.number_input("INV", 0, 160, 0)

# --- VISUALISATION & STATISTIQUES (NOUVEAU) ---
st.divider()
col_graph, col_stats = st.columns([1, 1.5])

# Dictionnaire des indices pour le graph
indices_principaux = {"ICV": icv, "IVS": ivs, "IRF": irf, "IMT": imt, "IVT": ivt}
# On retire les 0 pour les calculs
indices_valides = {k: v for k, v in indices_principaux.items() if v > 0}

with col_graph:
    st.subheader("📊 Profil (Radar)")
    if len(indices_valides) >= 3:
        fig = plot_radar_chart(indices_valides)
        if fig: st.pyplot(fig)
    else:
        st.info("Entrez au moins 3 indices pour voir le graphique.")

with col_stats:
    st.subheader("📈 Points Forts / Faibles (Perso)")
    if len(indices_valides) > 0:
        moyenne_perso = sum(indices_valides.values()) / len(indices_valides)
        st.markdown(f"**Moyenne de l'enfant : {moyenne_perso:.1f}**")
        
        txt_stats = ""
        for k, v in indices_valides.items():
            diff = v - moyenne_perso
            if diff >= 10:
                st.success(f"🟢 **{k} ({v})** : Point FORT (+{diff:.1f})")
                txt_stats += f"- {k} est un Point FORT personnel.\n"
            elif diff <= -10:
                st.error(f"🔴 **{k} ({v})** : Point FAIBLE ({diff:.1f})")
                txt_stats += f"- {k} est un Point FAIBLE personnel.\n"
            else:
                st.markdown(f"⚪ {k} ({v}) : Homogène")
    else:
        txt_stats = ""

# --- CLINIQUE (CHECKLIST) ---
st.divider()
st.subheader("4. Observations Cliniques (Checklist)")

col_check1, col_check2, col_check3 = st.columns(3)
obs_cliniques = []

with col_check1:
    st.markdown("**Attitude & Émotion**")
    if st.checkbox("Anxiété de performance"): obs_cliniques.append("Anxiété de performance")
    if st.checkbox("Opposition / Retrait"): obs_cliniques.append("Opposition ou retrait")
    if st.checkbox("Agitation motrice"): obs_cliniques.append("Agitation motrice")
    if st.checkbox("Impulsivité"): obs_cliniques.append("Impulsivité")

with col_check2:
    st.markdown("**Cognition**")
    if st.checkbox("Fatigabilité rapide"): obs_cliniques.append("Fatigabilité rapide")
    if st.checkbox("Défaut d'attention"): obs_cliniques.append("Défaut d'attention/Concentration")
    if st.checkbox("Besoin de relance"): obs_cliniques.append("Besoin fréquent de relance")
    if st.checkbox("Verbalisation abondante"): obs_cliniques.append("Verbalisation abondante")

with col_check3:
    st.markdown("**Outil / Graphisme**")
    if st.checkbox("Crispation graphique"): obs_cliniques.append("Crispation graphique")
    if st.checkbox("Lenteur graphique"): obs_cliniques.append("Lenteur graphique")
    if st.checkbox("Autocritique excessive"): obs_cliniques.append("Autocritique excessive")
    if st.checkbox("Gauchèrie visuelle"): obs_cliniques.append("Gêne visuo-motrice")

st.markdown("---")
# Zone texte libre pour ce qui n'est pas dans la liste
ana = st.text_area("Anamnèse / Scolarité", height=100)
obs_libre = st.text_area("Autres observations (Texte libre)", height=80)

# --- GENERATION ---
if st.button(f"✨ Lancer l'Analyse Complète", type="primary"):
    
    if total_chars > LIMIT_CHARS: st.error("Trop lourd !"); st.stop()

    infos = f"Enfant: {prenom}, {sexe}. Age: {ans} ans {mois} mois. Latéralité: {lateralite}."
    observations_compilees = ", ".join(obs_cliniques) + ". " + obs_libre
    
    data = "SCORES:\n"
    for k,v in indices_principaux.items():
        if v > 0: data += f"- Indice {k}: {v}\n"
    for k,v in {"IAG":iag, "ICC":icc, "INV":inv}.items():
        if v > 0: data += f"- Complémentaire {k}: {v}\n"
        
    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    for k,v in sub_map.items():
        if v > 0: data += f"- {k}: {v}\n"

    with st.spinner(f"Rédaction avec prise en compte du profil visuel et clinique..."):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Rôle: Expert WISC-V.
            CONTEXTE: {infos}
            ANAMNÈSE: {ana}
            
            OBSERVATIONS CLINIQUES (Crucial): {observations_compilees}
            
            RÉSULTATS:
            {data}
            
            ANALYSE STATISTIQUE (A utiliser pour justifier):
            Moyenne personnelle: {moyenne_perso if len(indices_valides)>0 else 'N/A'}
            {txt_stats}
            
            SOURCES: {knowledge_base}
            
            CONSIGNE:
            Rédige un compte-rendu complet (Partie III Interprétation + Partie IV Orientations).
            1. Utilise l'analyse statistique fournie pour identifier formellement les points forts/faibles PERSONNELS.
            2. Croise OBLIGATOIREMENT les items cochés dans les observations (ex: {observations_compilees}) avec les résultats.
            3. Partie IV: Recommandations concrètes (Pédagogie + Orientation).
            """
            
            res = model.generate_content(prompt)
            st.markdown("### Résultat :")
            st.markdown(res.text)
            
            filename = f"Bilan_{prenom}_{ans}ans.docx" if prenom else "Bilan.docx"
            docx_file = create_docx(res.text, prenom, f"{ans} ans {mois} mois")
            st.download_button("📄 Télécharger Word", docx_file, filename, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
        except Exception as e: st.error(f"Erreur : {e}")
