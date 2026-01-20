import streamlit as st
import google.generativeai as genai
import os
import io
from io import StringIO
from pypdf import PdfReader
from docx import Document
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Expert", page_icon="🧒", layout="wide")
st.title("🧠 Assistant WISC-V : Analyse Personnalisée")

# --- CONNEXION ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- FONCTION CALCUL AGE ---
def calculer_age(d_naiss, d_bilan):
    if d_bilan < d_naiss:
        return 0, 0
    ans = d_bilan.year - d_naiss.year
    mois = d_bilan.month - d_naiss.month
    if d_bilan.day < d_naiss.day:
        mois -= 1
    if mois < 0:
        ans -= 1
        mois += 12
    return ans, mois

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
    doc.add_heading(f'Analyse WISC-V : {prenom}', 0)
    doc.add_paragraph(f"Âge : {age_str}")
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
    st.caption("Cochez uniquement le nécessaire (Manuel Interprétation).")
    
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    if local_files:
        for f in local_files:
            # Par défaut décoché
            if st.checkbox(f"📄 {f}", value=False):
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
                total_chars += len(c)
    
    st.divider()
    if total_chars > LIMIT_CHARS:
        st.error(f"🛑 Trop lourd ({total_chars}) ! Décochez.")
    elif total_chars > 0:
        st.success("✅ Poids OK")

# --- INTERFACE PRINCIPALE ---

# 1. IDENTITÉ
st.subheader("1. Identité de l'enfant")
col_id1, col_id2, col_id3 = st.columns(3)

with col_id1:
    prenom = st.text_input("Prénom", placeholder="Ex: Lucas")
    sexe = st.radio("Sexe", ["Garçon", "Fille"], horizontal=True)

with col_id2:
    d_naiss = st.date_input("Date de naissance", value=date(2015, 1, 1), min_value=date(1900, 1, 1))
    lateralite = st.radio("Latéralité", ["Droitier", "Gaucher"], horizontal=True)

with col_id3:
    d_test = st.date_input("Date du bilan", value=date.today())
    # Calcul automatique
    ans, mois = calculer_age(d_naiss, d_test)
    st.markdown(f"### {ans} ans et {mois} mois")

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("2. Scores")
    c1, c2 = st.columns(2)
    with c1:
        qit = st.number_input("QIT", 0, 160, 0)
        icv = st.number_input("ICV", 0, 160, 0)
        ivs = st.number_input("IVS", 0, 160, 0)
    with c2:
        irf = st.number_input("IRF", 0, 160, 0)
        imt = st.number_input("IMT", 0, 160, 0)
        ivt = st.number_input("IVT", 0, 160, 0)

    with st.expander("Subtests (Notes Standard)"):
        sc1, sc2 = st.columns(2)
        with sc1:
            sim = st.number_input("Similitudes", 0, 19, 0)
            voc = st.number_input("Vocabulaire", 0, 19, 0)
            info = st.number_input("Info", 0, 19, 0)
            comp = st.number_input("Comp", 0, 19, 0)
            cub = st.number_input("Cubes", 0, 19, 0)
            puz = st.number_input("Puzzles", 0, 19, 0)
        with sc2:
            mat = st.number_input("Matrices", 0, 19, 0)
            bal = st.number_input("Balances", 0, 19, 0)
            arit = st.number_input("Arithmétique", 0, 19, 0)
            memc = st.number_input("Mém. Chiffres", 0, 19, 0)
            memi = st.number_input("Mém. Images", 0, 19, 0)
            seq = st.number_input("Séquence", 0, 19, 0)
            cod = st.number_input("Code", 0, 19, 0)
            sym = st.number_input("Symboles", 0, 19, 0)
            bar = st.number_input("Barrage", 0, 19, 0)

with col2:
    st.subheader("3. Clinique")
    ana = st.text_area("Anamnèse", height=150, placeholder="Motif, histoire scolaire, familiale...")
    obs = st.text_area("Observations", height=150, placeholder="Comportement pendant les épreuves...")

# --- GENERATION ---
if st.button(f"✨ Analyser le profil de {prenom if prenom else 'l\'enfant'}", type="primary"):
    
    if total_chars > LIMIT_CHARS:
        st.error("Trop de documents cochés !")
        st.stop()

    # Données compilées
    infos = f"Enfant: {prenom}, {sexe}. {ans} ans et {mois} mois. Latéralité: {lateralite}."
    
    data = "SCORES:\n"
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: data += f"- {k}: {v}\n"
    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    for k,v in sub_map.items():
        if v > 0: data += f"- {k}: {v}\n"

    with st.spinner(f"Rédaction de l'analyse pour {prenom}..."):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Rôle: Expert WISC-V.
            CONTEXTE: {infos}
            ANAMNÈSE: {ana}
            OBSERVATIONS: {obs}
            RÉSULTATS: {data}
            SOURCES: {knowledge_base}
            
            CONSIGNE:
            Rédige l'interprétation des résultats.
            Utilise le prénom "{prenom}" pour rendre le texte humain.
            Justifie tes hypothèses avec les sources théoriques.
            Sois vigilant sur les liens entre résultats et comportement (ex: agitation et indices de vitesse).
            """
            
            res = model.generate_content(prompt)
            
            st.markdown("### Résultat :")
            st.markdown(res.text)
            
            # Nom du fichier propre (ex: Analyse_Lucas.docx)
            filename = f"Analyse_{prenom}_{ans}ans.docx" if prenom else "Analyse_WISC.docx"
            docx_file = create_docx(res.text, prenom, f"{ans} ans {mois} mois")
            
            st.download_button(
                label="📄 Télécharger en Word",
                data=docx_file,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        except Exception as e:
            st.error(f"Erreur : {e}")
