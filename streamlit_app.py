import streamlit as st
import google.generativeai as genai
import os
import io
from io import StringIO
from pypdf import PdfReader
from docx import Document
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Expert Pro", page_icon="🎓", layout="wide")
st.title("🧠 Assistant WISC-V : Analyse & Orientations")

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

# --- SIDEBAR (Gestion Poids) ---
knowledge_base = ""
total_chars = 0
LIMIT_CHARS = 800000

with st.sidebar:
    st.header("📚 Bibliothèque")
    st.caption("Cochez uniquement le Manuel d'Interprétation.")
    
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

# ENFANT
with col_id1:
    st.markdown("##### 👤 L'Enfant")
    prenom = st.text_input("Prénom", placeholder="Ex: Lucas")
    sexe = st.radio("Sexe", ["Garçon", "Fille"], horizontal=True)
    lateralite = st.radio("Latéralité", ["Droitier", "Gaucher"], horizontal=True)

# NAISSANCE (3 cases)
with col_id2:
    st.markdown("##### 🎂 Date de Naissance")
    cn_jour, cn_mois, cn_annee = st.columns([1, 1, 1.5])
    with cn_jour:
        jj_n = st.number_input("Jour", 1, 31, 1, key="j_n")
    with cn_mois:
        mm_n = st.number_input("Mois", 1, 12, 1, key="m_n")
    with cn_annee:
        aa_n = st.number_input("Année", 2000, 2030, 2015, key="a_n")
    try: d_naiss = date(aa_n, mm_n, jj_n)
    except: d_naiss = date.today()

# BILAN (3 cases)
with col_id3:
    st.markdown("##### 📅 Date du Bilan")
    cb_jour, cb_mois, cb_annee = st.columns([1, 1, 1.5])
    with cb_jour:
        jj_b = st.number_input("Jour", 1, 31, date.today().day, key="j_b")
    with cb_mois:
        mm_b = st.number_input("Mois", 1, 12, date.today().month, key="m_b")
    with cb_annee:
        aa_b = st.number_input("Année", 2020, 2030, date.today().year, key="a_b")
    try: d_test = date(aa_b, mm_b, jj_b)
    except: d_test = date.today()
    
    ans, mois = calculer_age(d_naiss, d_test)
    st.success(f"Âge au bilan :\n### {ans} ans et {mois} mois")

st.divider()

col_scores, col_inputs = st.columns([1, 1])

with col_scores:
    st.subheader("2. Saisie des Subtests (Notes Standard)")
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
        seq = st.number_input("Séquence L-C", 0, 19, 0)
        bar = st.number_input("Barrage", 0, 19, 0)

with col_inputs:
    st.subheader("3. Indices")
    
    somme_iag = sim + voc + cub + mat + bal
    somme_icc = memc + memi + sym + cod
    somme_inv = cub + puz + mat + bal + memi + cod
    
    st.warning(f"🧮 **Aide Calcul (Sommes) :**\n- IAG = **{somme_iag}**\n- ICC = **{somme_icc}**\n- INV = **{somme_inv}**")
    
    ic1, ic2 = st.columns(2)
    with ic1:
        qit = st.number_input("QIT (Total)", 0, 160, 0)
        icv = st.number_input("ICV (Verbal)", 0, 160, 0)
        ivs = st.number_input("IVS (Visuel)", 0, 160, 0)
        irf = st.number_input("IRF (Fluide)", 0, 160, 0)
    with ic2:
        imt = st.number_input("IMT (Mémoire)", 0, 160, 0)
        ivt = st.number_input("IVT (Vitesse)", 0, 160, 0)
        st.markdown("---")
        iag = st.number_input("IAG (Aptitude G.)", 0, 160, 0)
        icc = st.number_input("ICC (Comp. Cogn.)", 0, 160, 0)
        inv = st.number_input("INV (Non Verbal)", 0, 160, 0)

st.divider()
st.subheader("4. Clinique & Scolarité")
ana = st.text_area("Anamnèse & Scolarité actuelle", height=100, placeholder="Ex: Enfant en CM1, difficultés lecture, suivi ortho...")
obs = st.text_area("Observations Comportementales", height=100, placeholder="Agitation, anxiété, opposition, fatigabilité...")

# --- GENERATION ---
if st.button(f"✨ Analyser et Préconiser pour {prenom if prenom else 'l\'enfant'}", type="primary"):
    
    if total_chars > LIMIT_CHARS: st.error("Trop lourd !"); st.stop()

    infos = f"Enfant: {prenom}, {sexe}. Age bilan: {ans} ans {mois} mois. Latéralité: {lateralite}."
    
    data = "SCORES:\n"
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: data += f"- Indice {k}: {v}\n"
    for k,v in {"IAG":iag, "ICC":icc, "INV (Non Verbal)":inv}.items():
        if v > 0: data += f"- Indice Complémentaire {k}: {v}\n"
    
    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    for k,v in sub_map.items():
        if v > 0: data += f"- {k}: {v}\n"

    with st.spinner(f"Rédaction de l'analyse et des orientations..."):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Rôle: Psychologue Expert WISC-V.
            CONTEXTE: {infos}
            ANAMNÈSE: {ana}
            OBSERVATIONS: {obs}
            RÉSULTATS:
            {data}
            SOURCES: {knowledge_base}
            
            CONSIGNE DE RÉDACTION STRUCTURÉE:
            
            1. INTERPRÉTATION DES RÉSULTATS (Partie III) :
               - Analyse l'homogénéité (QIT valide ?).
               - Compare IAG vs ICC et ICV vs INV si pertinents.
               - Fais des liens avec la clinique (ex: TDAH et chute IMT/IVT).
            
            2. RECOMMANDATIONS & ORIENTATIONS (Partie IV) :
               - Affiche cette partie clairement avec un titre "IV. Pistes de travail et Orientations".
               - PÉDAGOGIE : Propose des aménagements concrets en classe (ex: Tiers-temps, ordinateur, supports visuels, placement en classe) adaptés aux points faibles (ex: si IMT faible -> consignes courtes).
               - SOINS : Suggère des bilans complémentaires si nécessaire (Orthophonie, Psychomotricité, Attentionnel).
               - ORIENTATION SCOLAIRE :
                 * Si déficience intellectuelle ou troubles sévères : discute l'hypothèse ULIS (TFC, TSLA selon le profil) ou IMPro.
                 * Si difficultés scolaires massives mais QIT limite/normal faible : discute l'hypothèse SEGPA.
                 * Si troubles du comportement majeurs (mentionnés dans les obs) : discute l'hypothèse ITEP.
                 * Utilise toujours le conditionnel pour les orientations ("Une orientation vers... pourrait être discutée").
            
            Ton : Professionnel, nuancé, précis.
            """
            
            res = model.generate_content(prompt)
            st.markdown("### Résultat :")
            st.markdown(res.text)
            
            filename = f"Bilan_WISC_{prenom}_{ans}ans.docx" if prenom else "Bilan_WISC.docx"
            docx_file = create_docx(res.text, prenom, f"{ans} ans {mois} mois")
            st.download_button("📄 Télécharger Word", docx_file, filename, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
        except Exception as e: st.error(f"Erreur : {e}")
