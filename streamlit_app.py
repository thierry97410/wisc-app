import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Standard", page_icon="🧠", layout="wide")
st.title("🧠 Assistant WISC-V : Version Standard")

# --- CONNEXION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur : Clé API manquante.")
    st.stop()

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

# --- SIDEBAR (RESTREINTE) ---
knowledge_base = ""
doc_count = 0

with st.sidebar:
    st.header("📚 Documents")
    st.warning("⚠️ Mode 'Standard' actif (gemini-pro). Sélectionnez 1 seul manuel à la fois pour éviter la saturation mémoire.")
    
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    for f in local_files:
        # Par défaut, tout est DÉCOCHÉ pour éviter le crash immédiat
        if st.checkbox(f"📄 {f}", value=False):
            c = read_file(f, f)
            knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
            doc_count += 1

    if doc_count > 1:
        st.error("⚠️ Attention : Plus d'un document sélectionné. Le modèle risque de saturer.")

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Scores")
    c1, c2 = st.columns(2)
    with c1:
        qit = st.number_input("QIT", 0, 160, 0)
        icv = st.number_input("ICV", 0, 160, 0)
        ivs = st.number_input("IVS", 0, 160, 0)
    with c2:
        irf = st.number_input("IRF", 0, 160, 0)
        imt = st.number_input("IMT", 0, 160, 0)
        ivt = st.number_input("IVT", 0, 160, 0)
    
    with st.expander("Subtests"):
        sc1, sc2 = st.columns(2)
        with sc1:
            sim = st.number_input("Similitudes", 0, 19, 0)
            voc = st.number_input("Vocabulaire", 0, 19, 0)
            info = st.number_input("Info", 0, 19, 0)
            comp = st.number_input("Compréhension", 0, 19, 0)
            cub = st.number_input("Cubes", 0, 19, 0)
            puz = st.number_input("Puzzles", 0, 19, 0)
        with sc2:
            mat = st.number_input("Matrices", 0, 19, 0)
            bal = st.number_input("Balances", 0, 19, 0)
            arit = st.number_input("Arithmétique", 0, 19, 0)
            memc = st.number_input("Mém. Chiffres", 0, 19, 0)
            memi = st.number_input("Mém. Images", 0, 19, 0)
            seq = st.number_input("Séquence L-C", 0, 19, 0)
            cod = st.number_input("Code", 0, 19, 0)
            sym = st.number_input("Symboles", 0, 19, 0)
            bar = st.number_input("Barrage", 0, 19, 0)

with col2:
    st.subheader("2. Clinique")
    ana = st.text_area("Anamnèse", height=200)
    obs = st.text_area("Observations", height=200)

# --- GENERATION ---
if st.button("✨ Analyser", type="primary"):
    
    scores = "SCORES:\n"
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: scores += f"- {k}: {v}\n"
    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    for k,v in sub_map.items():
        if v > 0: scores += f"- {k}: {v}\n"

    with st.spinner("Analyse (Modèle Standard v1.0)..."):
        try:
            # ON FORCE LE VIEUX MODELE SOLIDE
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            Expert WISC-V.
            
            SOURCE DOCUMENTAIRE :
            {knowledge_base}
            
            DONNÉES :
            - Anamnèse: {ana}
            - Obs: {obs}
            - {scores}
            
            CONSIGNE:
            Rédige l'évaluation psychométrique (Partie III).
            Utilise la source documentaire si disponible pour justifier.
            Fais des liens cliniques.
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            
        except Exception as e:
            st.error(f"Erreur : {e}")
            
