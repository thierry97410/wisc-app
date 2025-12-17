import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIG ---
st.set_page_config(page_title="WISC-V Expert", page_icon="🧠", layout="wide")
st.title("🧠 Assistant WISC-V : Expert")

# --- API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- LECTURE ---
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

# --- SIDEBAR (DOCS) ---
knowledge_base = ""
with st.sidebar:
    st.header("📚 Documents")
    
    # Fichiers locaux
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    if local_files:
        st.info("Décochez si erreur de quota.")
        for f in local_files:
            if st.checkbox(f, value=True):
                c = read_file(f, f)
                knowledge_base += f"\n--- REF: {f} ---\n{c}\n"
    
    st.divider()
    # Upload
    uploads = st.file_uploader("Ajout (+)", type=['pdf', 'txt'], accept_multiple_files=True)
    if uploads:
        for u in uploads:
            c = read_file(u, u.name)
            knowledge_base += f"\n--- SUPP: {u.name} ---\n{c}\n"

# --- INTERFACE ---
col1, col2 = st.columns(2)
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
            cub = st.number_input("Cubes", 0, 19, 0)
            puz = st.number_input("Puzzles", 0, 19, 0)
            info = st.number_input("Info", 0, 19, 0)
            comp = st.number_input("Compréhension", 0, 19, 0)
        with sc2:
            mat = st.number_input("Matrices", 0, 19, 0)
            bal = st.number_input("Balances", 0, 19, 0)
            memc = st.number_input("Mém. Chiffres", 0, 19, 0)
            cod = st.number_input("Code", 0, 19, 0)
            sym = st.number_input("Symboles", 0, 19, 0)
            memi = st.number_input("Mém. Images", 0, 19, 0)

with col2:
    st.subheader("2. Clinique")
    ana = st.text_area("Anamnèse", height=150)
    obs = st.text_area("Observations", height=150)

# --- GENERATION ---
if st.button("✨ Analyser", type="primary"):
    # Construction des données
    data = "SCORES:\n"
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v>0: data += f"- {k}: {v}\n"
    for k,v in {"Sim":sim,"Voc":voc,"Cub":cub,"Puz":puz,"Mat":mat,"Bal":bal,"MemC":memc,"Code":cod,"Sym":sym,"Info":info,"Comp":comp,"MemI":memi}.items():
        if v>0: data += f"- {k}: {v}\n"

    with st.spinner("Analyse..."):
        try:
            # On tente le modèle Flash standard
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""Expert WISC-V. 
            BASES: {knowledge_base}
            CAS: {ana} / {obs} / {data}
            TÂCHE: Rédiger analyse psychométrique III.
            Utiliser les bases pour justifier. Citer écarts-types."""
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
        except Exception as e:
            st.error(f"Erreur : {e}")
            st.warning("Essayez de décocher des documents à gauche.")
