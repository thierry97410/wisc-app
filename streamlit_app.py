import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Auto-Détection", page_icon="🧠", layout="wide")
st.title("🧠 Assistant WISC-V : Expert")

# --- CONNEXION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur : Clé API manquante.")
    st.stop()

# --- DÉTECTION AUTOMATIQUE DU MODÈLE (C'est la partie magique) ---
# On ne devine plus le nom, on le demande à l'API.
found_model = None

try:
    with st.spinner("Recherche du meilleur modèle disponible pour votre région..."):
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 1. Priorité absolue : Un modèle FLASH (gratuit et gros volume)
        for model in available_models:
            if "flash" in model.lower():
                found_model = model
                break # On prend le premier Flash trouvé
        
        # 2. Si pas de Flash, on cherche le PRO (attention au quota)
        if not found_model:
            for model in available_models:
                if "pro" in model.lower() and "vision" not in model.lower():
                    found_model = model
                    break
        
        # 3. Secours ultime
        if not found_model:
            found_model = "models/gemini-pro"

    # Affichage du résultat de la recherche
    st.success(f"✅ Modèle connecté : **{found_model}**")
    # On nettoie le nom pour l'utiliser (enlève 'models/' si présent parfois)
    FINAL_MODEL_NAME = found_model

except Exception as e:
    st.error(f"Erreur de connexion Google : {e}")
    st.stop()


# --- FONCTION LECTURE ---
def read_file_content(file_obj, filename):
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

# --- CHARGEMENT DOCS ---
knowledge_base = ""
files_loaded = []
for filename in os.listdir('.'):
    if filename.lower().endswith(('.txt', '.pdf')) and filename not in ["requirements.txt", "app.py"]:
        c = read_file_content(filename, filename)
        if c:
            knowledge_base += f"\n--- REF: {filename} ---\n{c}\n"
            files_loaded.append(filename)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📚 Bibliothèque")
    if files_loaded:
        st.info(f"{len(files_loaded)} docs chargés.")
        with st.expander("Voir liste"):
            for f in files_loaded: st.caption(f"- {f}")
    
    st.divider()
    uploaded_files = st.file_uploader("Ajout (+)", type=['txt', 'pdf'], accept_multiple_files=True)
    if uploaded_files:
        for u in uploaded_files:
            c = read_file_content(u, u.name)
            knowledge_base += f"\n--- REF SUPP: {u.name} ---\n{c}\n"
        st.success("Docs ajoutés !")

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Données Chiffrées")
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

    with st.spinner(f"Rédaction en cours avec {FINAL_MODEL_NAME}..."):
        try:
            # Utilisation du modèle détecté automatiquement
            model = genai.GenerativeModel(FINAL_MODEL_NAME)
            
            prompt = f"""
            Psychologue expert WISC-V.
            
            MANUELS RÉFÉRENCE:
            {knowledge_base}
            
            CAS PATIENT:
            - Anamnèse: {anamnese}
            - Obs: {observations}
            - {d_str}
            
            CONSIGNES:
            Rédige l'évaluation psychométrique (Partie III).
            1. Utilise les manuels pour interpréter les scores (théorie CHC etc).
            2. Calcule/mentionne les écarts-types.
            3. Croise observations et résultats.
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            
        except Exception as e:
            st.error(f"Erreur technique : {e}")
