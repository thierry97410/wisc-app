import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Pro (Flash)", page_icon="⚡", layout="wide")
st.title("⚡ Assistant WISC-V : Expert & Documenté")

# --- CONNEXION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur : Clé API manquante dans les secrets.")
    st.stop()

# --- FONCTION DE LECTURE ROBUSTE ---
def read_file_content(file_obj, filename):
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            pdf_reader = PdfReader(file_obj)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
        else:
            if isinstance(file_obj, str): 
                with open(file_obj, "r", encoding="utf-8") as f:
                    text = f.read()
            else: 
                stringio = StringIO(file_obj.getvalue().decode("utf-8"))
                text = stringio.read()
    except Exception as e:
        st.warning(f"Lecture impossible pour {filename}")
    return text

# --- CHARGEMENT AUTOMATIQUE DES DOCS ---
knowledge_base = ""
files_loaded = []
# On scanne le dossier
for filename in os.listdir('.'):
    if filename.lower().endswith(('.txt', '.pdf')) and filename not in ["requirements.txt", "app.py"]:
        content = read_file_content(filename, filename)
        if content:
            knowledge_base += f"\n--- DOCUMENT RÉFÉRENCE: {filename} ---\n{content}\n"
            files_loaded.append(filename)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📚 Bibliothèque")
    if files_loaded:
        st.success(f"{len(files_loaded)} manuels chargés en mémoire.")
        with st.expander("Voir les fichiers"):
            for f in files_loaded:
                st.caption(f"📄 {f}")
    else:
        st.warning("Aucun manuel trouvé. Uploadez vos PDF sur GitHub.")

    st.divider()
    st.info("ℹ️ Modèle utilisé : **Gemini 1.5 Flash** (Gratuit & Rapide). Idéal pour l'analyse de gros volumes de texte.")

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Indices & Scores")
    c1, c2 = st.columns(2)
    with c1:
        qit = st.number_input("QIT", 0, 160, 0)
        icv = st.number_input("ICV", 0, 160, 0)
        ivs = st.number_input("IVS", 0, 160, 0)
    with c2:
        irf = st.number_input("IRF", 0, 160, 0)
        imt = st.number_input("IMT", 0, 160, 0)
        ivt = st.number_input("IVT", 0, 160, 0)

    with st.expander("📝 Détail des Subtests", expanded=True):
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
    anamnese = st.text_area("Contexte", height=200, placeholder="Motif, histoire...")
    observations = st.text_area("Observations", height=200, placeholder="Comportement...")

# --- GENERATION ---
if st.button("✨ Lancer l'Analyse", type="primary"):
    
    # Formatage des données
    data_str = "SCORES DISPONIBLES:\n"
    for k, v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: data_str += f"- Indice {k}: {v}\n"
        
    sub_map = {"Sim":sim, "Voc":voc, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "MemChif":mem_c, "Code":cod, "Sym":sym, "Info":info, "Comp":comp, "MemImg":mem_i}
    for k, v in sub_map.items():
        if v > 0: data_str += f"- Subtest {k}: {v}\n"

    with st.spinner("Lecture des manuels et analyse en cours..."):
        try:
            # ON UTILISE LE MODELE FLASH (Le plus robuste pour le gratuit)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Tu es un psychologue expert spécialisé dans le WISC-V.
            
            ### BASE DE CONNAISSANCES (Tes manuels de référence) :
            {knowledge_base}
            
            ### LE CAS DU PATIENT :
            - Anamnèse : {anamnese}
            - Observations : {observations}
            - {data_str}
            
            ### TÂCHE :
            Rédige la partie "III. Évaluation Psychométrique" du bilan.
            
            ### CONSIGNES EXPERTES :
            1. **Intégration Théorique :** Utilise impérativement les manuels fournis pour justifier tes interprétations (ex: citer les hypothèses CHC si pertinentes dans les textes).
            2. **Statistiques :** Situe chaque score significatif en termes d'écart-type.
            3. **Clinique :** Ne fais pas une lecture "froide" des chiffres. Explique les scores par les observations (ex: "La chute en Code corrobore la fatigabilité observée...").
            4. **Style :** Professionnel, nuancé, paragraphes structurés.
            """
            
            # Appel API
            res = model.generate_content(prompt)
            st.markdown(res.text)
            
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
            st.info("Si l'erreur persiste, attendez 1 minute (limite de quota) et réessayez.")
