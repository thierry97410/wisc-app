import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Futur", page_icon="🚀", layout="wide")
st.title("🧠 Assistant WISC-V : Modèle Expérimental")

# --- CONNEXION ---
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

# --- SIDEBAR (Gestion du Poids) ---
knowledge_base = ""
total_chars = 0
LIMIT_CHARS = 800000 # Environ 200k tokens (marge de sécurité pour le 2.5 Flash)

with st.sidebar:
    st.header("📚 Bibliothèque & Quota")
    st.caption("Le modèle Gemini 2.5 est puissant mais limité en quantité. **Gardez la jauge dans le VERT.**")
    
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    # Sélecteur
    if local_files:
        for f in local_files:
            # Par défaut, on ne coche RIEN pour te laisser choisir
            if st.checkbox(f"📄 {f}", value=False):
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
                total_chars += len(c)
    
    st.divider()
    
    # JAUGE DE POIDS
    st.markdown(f"**Volume actuel : {total_chars} caractères**")
    if total_chars > LIMIT_CHARS:
        st.error(f"🛑 STOP ! Trop lourd ({total_chars}). Décochez des livres sinon erreur 429.")
    elif total_chars > 0:
        st.success("✅ Volume OK. Vous pouvez lancer.")
    else:
        st.info("Cochez au moins 1 livre.")

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
    ana = st.text_area("Anamnèse", height=150)
    obs = st.text_area("Observations", height=150)

# --- GENERATION ---
if st.button("✨ Analyser (Gemini 2.5 Flash)", type="primary"):
    
    if total_chars > LIMIT_CHARS:
        st.error("Volume trop élevé. Décochez des documents à gauche.")
        st.stop()

    data = "SCORES:\n"
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: data += f"- {k}: {v}\n"
    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    for k,v in sub_map.items():
        if v > 0: data += f"- {k}: {v}\n"

    with st.spinner("Analyse futuriste en cours..."):
        try:
            # ON UTILISE CELUI QUE TU AS DANS TA LISTE
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            Rôle: Expert WISC-V.
            
            SOURCES:
            {knowledge_base}
            
            DONNÉES:
            - Anamnèse: {ana}
            - Obs: {obs}
            - {data}
            
            CONSIGNE:
            Rédige l'analyse psychométrique (Partie III).
            Utilise les sources pour justifier les hypothèses.
            Sois précis.
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            
        except Exception as e:
            st.error(f"Erreur : {e}")
            if "429" in str(e):
                st.error("💀 QUOTA DÉPASSÉ : Décochez encore un livre, c'est trop lourd pour ce modèle !")
