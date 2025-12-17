import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Pro (15 Subtests)", page_icon="🧠", layout="wide")
st.title("🧠 Assistant WISC-V : Expert & Documenté")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- FONCTION DE LECTURE (PDF & TXT) ---
def read_file_content(file_obj, filename):
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            pdf_reader = PdfReader(file_obj)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        else:
            if isinstance(file_obj, str): 
                with open(file_obj, "r", encoding="utf-8") as f:
                    text = f.read()
            else: 
                stringio = StringIO(file_obj.getvalue().decode("utf-8"))
                text = stringio.read()
    except Exception as e:
        st.error(f"Erreur lecture {filename}: {e}")
    return text

# --- CHARGEMENT AUTOMATIQUE DOCS ---
knowledge_base = ""
files_loaded = []
for filename in os.listdir('.'):
    if filename.lower().endswith(('.txt', '.pdf')) and filename not in ["requirements.txt", "app.py"]:
        content = read_file_content(filename, filename)
        if content:
            knowledge_base += f"\n--- REF: {filename} ---\n{content}\n"
            files_loaded.append(filename)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📚 Base Documentaire")
    if files_loaded:
        st.success(f"{len(files_loaded)} documents actifs.")
        with st.expander("Voir liste"):
            for f in files_loaded:
                st.write(f"- {f}")
    else:
        st.info("Aucun document trouvé.")
    
    st.markdown("---")
    uploaded_files = st.file_uploader("Ajout manuel", type=['txt', 'pdf'], accept_multiple_files=True)
    if uploaded_files:
        for u in uploaded_files:
            c = read_file_content(u, u.name)
            knowledge_base += f"\n--- REF SUPP: {u.name} ---\n{c}\n"
        st.success("Documents ajoutés !")

# --- INTERFACE ---
st.info("💡 Note : Laissez la valeur à **0** si le subtest n'a pas été administré. (Notes Standard de 1 à 19)")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Indices (Notes Composites)")
    # Indices
    c_i1, c_i2 = st.columns(2)
    with c_i1:
        qit = st.number_input("QIT Total", 40, 160, 100)
        icv = st.number_input("ICV (Verbal)", 40, 160, 100)
        ivs = st.number_input("IVS (Visuospatial)", 40, 160, 100)
    with c_i2:
        irf = st.number_input("IRF (Fluide)", 40, 160, 100)
        imt = st.number_input("IMT (Mémoire)", 40, 160, 100)
        ivt = st.number_input("IVT (Vitesse)", 40, 160, 100)

    st.markdown("---")
    st.subheader("2. Les 15 Subtests (Notes Standard)")
    
    with st.expander("🗣️ Compréhension Verbale", expanded=True):
        sc1, sc2 = st.columns(2)
        with sc1:
            sim = st.number_input("Similitudes", 0, 19, 0)
            voc = st.number_input("Vocabulaire", 0, 19, 0)
        with sc2:
            info = st.number_input("Information (Opt)", 0, 19, 0)
            comp = st.number_input("Compréhension (Opt)", 0, 19, 0)

    with st.expander("🧩 Visuospatial", expanded=True):
        sc3, sc4 = st.columns(2)
        with sc3:
            cub = st.number_input("Cubes", 0, 19, 0)
        with sc4:
            puz = st.number_input("Puzzles Visuels", 0, 19, 0)

    with st.expander("⚖️ Raisonnement Fluide", expanded=True):
        sc5, sc6 = st.columns(2)
        with sc5:
            mat = st.number_input("Matrices", 0, 19, 0)
            bal = st.number_input("Balances", 0, 19, 0)
        with sc6:
            arit = st.number_input("Arithmétique (Opt)", 0, 19, 0)

    with st.expander("🧠 Mémoire de Travail", expanded=True):
        sc7, sc8 = st.columns(2)
        with sc7:
            mem_c = st.number_input("Mém. Chiffres", 0, 19, 0)
            mem_i = st.number_input("Mém. Images", 0, 19, 0)
        with sc8:
            seq = st.number_input("Séq. Lettres-Chiffres (Opt)", 0, 19, 0)

    with st.expander("⚡ Vitesse de Traitement", expanded=True):
        sc9, sc10 = st.columns(2)
        with sc9:
            cod = st.number_input("Code", 0, 19, 0)
            sym = st.number_input("Symboles", 0, 19, 0)
        with sc10:
            bar = st.number_input("Barrage (Opt)", 0, 19, 0)

with col2:
    st.subheader("3. Clinique & Observations")
    anamnese = st.text_area("Contexte / Anamnèse", height=200)
    observations = st.text_area("Observations pendant le test", height=200)

# --- LOGIQUE DE GENERATION ---
if st.button("✨ Analyser le profil complet", type="primary"):
    
    # Construction de la liste des subtests administrés uniquement
    subtests_str = ""
    scores_map = {
        "Similitudes": sim, "Vocabulaire": voc, "Information": info, "Compréhension": comp,
        "Cubes": cub, "Puzzles": puz,
        "Matrices": mat, "Balances": bal, "Arithmétique": arit,
        "Mém. Chiffres": mem_c, "Mém. Images": mem_i, "Séquence L-C": seq,
        "Code": cod, "Symboles": sym, "Barrage": bar
    }
    
    for name, score in scores_map.items():
        if score > 0: # On ne garde que ce qui a été passé
            subtests_str += f"- {name}: {score}\n"
    
    if subtests_str == "":
        subtests_str = "Aucun subtest saisi."

    with st.spinner("Analyse experte en cours..."):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Rôle : Psychologue expert WISC-V.
        Tâche : Rédiger la section "Évaluation Psychométrique" détaillée.
        
        BIBLIOTHÈQUE DE RÉFÉRENCE (Documents fournis) :
        {knowledge_base}
        
        DONNÉES DU PATIENT :
        - Contexte : {anamnese}
        - Observations : {observations}
        
        SCORES INDICES (M=100, ET=15) :
        - QIT={qit}, ICV={icv}, IVS={ivs}, IRF={irf}, IMT={imt}, IVT={ivt}
        
        SCORES SUBTESTS ADMINISTRÉS (M=10, ET=3) :
        {subtests_str}
        
        CONSIGNES DE RÉDACTION :
        1. Utilise tes connaissances ET les documents fournis pour interpréter les scores.
        2. Situe chaque indice et subtest significatif en termes d'Écarts-Types par rapport à la moyenne.
        3. Analyse les points forts et les points faibles (Forces/Faiblesses).
        4. Croise impérativement les résultats chiffrés avec les observations cliniques (ex: lien anxiété/vitesse, attention/mémoire).
        5. Sois vigilant sur l'homogénéité du QIT.
        """
        
        try:
            res = model.generate_content(prompt)
            st.markdown(res.text)
        except Exception as e:
            st.error(f"Erreur : {e}")
