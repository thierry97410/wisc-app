import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Expert (Sélectif)", page_icon="⚖️", layout="wide")
st.title("⚖️ Assistant WISC-V : Gestion de Documents")

# --- CONNEXION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- FONCTION LECTURE ---
def read_file_content(file_obj, filename):
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            pdf_reader = PdfReader(file_obj)
            # On limite la lecture pour éviter d'exploser les quotas si le livre est énorme
            # On lit tout, mais on garde en tête que c'est lourd
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

# --- SIDEBAR : GESTION INTELLIGENTE DES DOCS ---
knowledge_base = ""
total_chars = 0

with st.sidebar:
    st.header("📚 Documents Disponibles")
    
    # 1. Scan des fichiers présents
    found_files = [f for f in os.listdir('.') if f.lower().endswith(('.txt', '.pdf')) and f not in ["requirements.txt", "app.py"]]
    
    # 2. Sélecteur (Checkboxes)
    st.info("Cochez uniquement les livres nécessaires pour éviter l'erreur de Quota (429).")
    selected_files = []
    
    if found_files:
        st.markdown("**Fichiers sur le serveur :**")
        for f in found_files:
            # Par défaut, on coche tout, mais l'utilisateur peut décocher
            if st.checkbox(f"📄 {f}", value=True):
                content = read_file_content(f, f)
                if content:
                    knowledge_base += f"\n--- LIVRE : {f} ---\n{content}\n"
                    selected_files.append(f)
                    total_chars += len(content)
    
    st.divider()
    
    # 3. Upload manuel
    uploaded_files = st.file_uploader("Ajout temporaire", type=['txt', 'pdf'], accept_multiple_files=True)
    if uploaded_files:
        for u in uploaded_files:
            c = read_file_content(u, u.name)
            knowledge_base += f"\n--- UPLOAD : {u.name} ---\n{c}\n"
            total_chars += len(c)
            selected_files.append(u.name)

    # Indicateur de poids
    if total_chars > 500000:
        st.warning(f"⚠️ Volume très lourd : {total_chars} caractères. Risque d'erreur 429 élevé. Décochez des livres si ça plante.")
    else:
        st.success(f"Volume actuel : {total_chars} caractères (OK).")

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

    with st.expander("Subtests", expanded=True):
        sc1, sc2 = st.columns(2)
        with sc1:
            sim = st.number_input("Similitudes", 0, 19, 0)
            voc = st.number_input("Vocabulaire", 0, 19, 0)
            cub = st.number_input("Cubes", 0, 19, 0)
            puz = st.number_input("Puzzles", 0, 19, 0)
            info = st.number_input("Information", 0, 19, 0)
            comp = st.number_input("Compréhension", 0, 19, 0)
        with sc2:
            mat = st.number_input("Matrices", 0, 19, 0)
            bal = st.number_input("Balances", 0, 19, 0)
            mem_c = st.number_input("Mém. Chiffres", 0, 19, 0)
            cod = st.number_input("Code", 0, 19, 0)
            sym = st.number_input("Symboles", 0, 19, 0)
            mem_i = st.number_input("Mém. Images", 0, 19, 0)

with col2:
    st.subheader("2. Clinique")
    anamnese = st.text_area("Contexte", height=200)
    observations = st.text_area("Observations", height=200)

# --- GENERATION ---
if st.button("✨ Lancer l'Analyse", type="primary"):
    
    # Formatage
    d_str = "SCORES:\n"
    for k, v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: d_str += f"- {k}: {v}\n"
    s_map = {"Sim":sim, "Voc":voc, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "MemChif":mem_c, "Code":cod, "Sym":sym, "Info":info, "Comp":comp, "MemImg":mem_i}
    for k, v in s_map.items():
        if v > 0: d_str += f"- {k}: {v}\n"

    with st.spinner("Analyse en cours (Modèle Flash Standard)..."):
        try:
            # ON FORCE LE RETOUR AU CLASSIQUE (Moins de bugs de quota que le 2.5)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Rôle : Psychologue Expert.
            
            SOURCES SELECTIONNÉES :
            {knowledge_base}
            
            CAS :
            - Anamnèse: {anamnese}
            - Obs: {observations}
            - {d_str}
            
            CONSIGNE :
            Rédige l'analyse psychométrique (Partie III). 
            Utilise les sources pour justifier théoriquement.
            Sois précis sur les écarts-types.
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            
        except Exception as e:
            st.error(f"Erreur : {e}")
            st.warning("⚠️ Conseil : Décochez 1 ou 2 livres dans la barre de gauche et réessayez.")
