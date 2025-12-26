import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Expert (France)", page_icon="🇫🇷", layout="wide")
st.title("🧠 Assistant WISC-V : Expert & Documenté")

# --- CONNEXION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur : Clé API manquante dans les secrets.")
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

# --- SIDEBAR ---
knowledge_base = ""
files_loaded = []
total_chars = 0

with st.sidebar:
    st.header("📚 Documents")
    
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    if local_files:
        st.success(f"{len(local_files)} documents détectés.")
        st.info("💡 Astuce : Si ça plante, décochez les livres inutiles (ex: Administration).")
        
        for f in local_files:
            if st.checkbox(f"Utiliser : {f}", value=True):
                c = read_file(f, f)
                if c: 
                    knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
                    files_loaded.append(f)
                    total_chars += len(c)
    
    st.divider()
    uploads = st.file_uploader("Ajout manuel (+)", type=['pdf', 'txt'], accept_multiple_files=True)
    if uploads:
        for u in uploads:
            c = read_file(u, u.name)
            knowledge_base += f"\n--- UPLOAD: {u.name} ---\n{c}\n"
            total_chars += len(c)
            files_loaded.append(u.name)

    # Indicateur de poids pour vous aider
    if total_chars > 800000:
        st.warning(f"⚠️ Volume très lourd ({total_chars} caractères). Risque de saturation.")
    else:
        st.caption(f"Volume actuel : {total_chars} caractères (OK)")

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Résultats Chiffrés")
    c1, c2 = st.columns(2)
    with c1:
        qit = st.number_input("QIT", 0, 160, 0)
        icv = st.number_input("ICV", 0, 160, 0)
        ivs = st.number_input("IVS", 0, 160, 0)
    with c2:
        irf = st.number_input("IRF", 0, 160, 0)
        imt = st.number_input("IMT", 0, 160, 0)
        ivt = st.number_input("IVT", 0, 160, 0)

    with st.expander("Détail des Subtests", expanded=True):
        sc1, sc2 = st.columns(2)
        with sc1:
            sim = st.number_input("Similitudes", 0, 19, 0)
            voc = st.number_input("Vocabulaire", 0, 19, 0)
            info = st.number_input("Information", 0, 19, 0)
            comp = st.number_input("Compréhension", 0, 19, 0)
            cub = st.number_input("Cubes", 0, 19, 0)
            puz = st.number_input("Puzzles", 0, 19, 0)
            mat = st.number_input("Matrices", 0, 19, 0)
            bal = st.number_input("Balances", 0, 19, 0)
        with sc2:
            arit = st.number_input("Arithmétique", 0, 19, 0)
            memc = st.number_input("Mém. Chiffres", 0, 19, 0)
            memi = st.number_input("Mém. Images", 0, 19, 0)
            seq = st.number_input("Séquence L-C", 0, 19, 0)
            cod = st.number_input("Code", 0, 19, 0)
            sym = st.number_input("Symboles", 0, 19, 0)
            bar = st.number_input("Barrage", 0, 19, 0)

with col2:
    st.subheader("2. Contexte")
    ana = st.text_area("Anamnèse", height=200, placeholder="Motif, histoire...")
    obs = st.text_area("Observations", height=200, placeholder="Comportement...")

# --- GENERATION ---
if st.button("✨ Lancer l'Analyse (Gemini 1.5)", type="primary"):
    
    data = "SCORES:\n"
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: data += f"- Indice {k}: {v} (M=100, ET=15)\n"
    
    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    for k,v in sub_map.items():
        if v > 0: data += f"- {k}: {v} (M=10, ET=3)\n"

    with st.spinner("Analyse experte en cours..."):
        try:
            # RETOUR AU MODÈLE 1.5 FLASH (1 Million de tokens !)
            # Il doit fonctionner maintenant que vous êtes en France.
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Tu es un psychologue expert WISC-V.
            
            SOURCES THÉORIQUES (Base-toi dessus):
            {knowledge_base}
            
            CAS CLINIQUE:
            - Anamnèse: {ana}
            - Observations: {obs}
            - Résultats:
            {data}
            
            CONSIGNE:
            Rédige l'analyse psychométrique (Partie III).
            1. Vérifie la validité du QIT.
            2. Justifie chaque interprétation par les textes théoriques fournis.
            3. Croise les résultats avec les observations.
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            
        except Exception as e:
            st.error(f"Erreur : {e}")
            if "429" in str(e):
                st.warning("⚠️ Trop de documents ! Décochez le 'Manuel d'Administration' dans la barre de gauche, il est très lourd et inutile pour l'interprétation.")
