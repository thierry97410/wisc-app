import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Auto-Expert", page_icon="🧠", layout="wide")
st.title("🧠 Assistant WISC-V : Expert & Documenté")

# --- CONNEXION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur critique : Clé API manquante dans les secrets.")
    st.stop()

# --- DIAGNOSTIC & SÉLECTION DU MODÈLE (NOUVEAU) ---
with st.sidebar:
    st.header("⚙️ Configuration IA")
    
    # On récupère la liste des modèles disponibles pour VOTRE clé
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # S'il n'y a pas de modèles 1.5, on prévient
        model_options = [m for m in available_models if "gemini" in m]
        
        if not model_options:
            st.error("Aucun modèle Gemini trouvé pour cette clé.")
            selected_model_name = "gemini-pro" # Fallback
        else:
            # On met le 1.5 Flash en premier s'il existe, sinon le Pro
            default_ix = 0
            for i, name in enumerate(model_options):
                if "flash" in name:
                    default_ix = i
                    break
            
            selected_model_name = st.selectbox(
                "🤖 Modèle utilisé", 
                model_options, 
                index=default_ix,
                help="Si un modèle échoue, essayez-en un autre dans la liste."
            )
            st.success(f"Modèle actif : {selected_model_name}")

    except Exception as e:
        st.error(f"Erreur de connexion Google : {e}")
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
        st.warning(f"Impossible de lire {filename}: {e}")
    return text

# --- CHARGEMENT DES DOCS ---
knowledge_base = ""
files_loaded = []
for filename in os.listdir('.'):
    if filename.lower().endswith(('.txt', '.pdf')) and filename not in ["requirements.txt", "app.py"]:
        content = read_file_content(filename, filename)
        if content:
            knowledge_base += f"\n--- REF: {filename} ---\n{content}\n"
            files_loaded.append(filename)

# --- SUITE SIDEBAR ---
with st.sidebar:
    st.header("📚 Base Documentaire")
    if files_loaded:
        st.info(f"{len(files_loaded)} documents chargés.")
        with st.expander("Voir liste"):
            for f in files_loaded:
                st.write(f"- {f}")
    
    st.markdown("---")
    uploaded_files = st.file_uploader("Ajout manuel", type=['txt', 'pdf'], accept_multiple_files=True)
    if uploaded_files:
        for u in uploaded_files:
            c = read_file_content(u, u.name)
            knowledge_base += f"\n--- REF SUPP: {u.name} ---\n{c}\n"
        st.success("Docs ajoutés !")

# --- INTERFACE PRINCIPALE ---
st.info("💡 **Consigne :** Laissez à **0** les épreuves non administrées.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Indices (Notes Composites)")
    c_i1, c_i2 = st.columns(2)
    with c_i1:
        qit = st.number_input("QIT Total", 0, 160, 0)
        icv = st.number_input("ICV (Verbal)", 0, 160, 0)
        ivs = st.number_input("IVS (Visuospatial)", 0, 160, 0)
    with c_i2:
        irf = st.number_input("IRF (Fluide)", 0, 160, 0)
        imt = st.number_input("IMT (Mémoire)", 0, 160, 0)
        ivt = st.number_input("IVT (Vitesse)", 0, 160, 0)

    st.markdown("---")
    st.subheader("2. Les Subtests (Notes Standard)")
    
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

# --- GENERATION ---
if st.button("✨ Analyser le profil", type="primary"):
    
    # Filtrage des données > 0
    indices_str = ""
    for name, score in {"QIT": qit, "ICV": icv, "IVS": ivs, "IRF": irf, "IMT": imt, "IVT": ivt}.items():
        if score > 0: indices_str += f"- {name}: {score} (M=100, ET=15)\n"
    if not indices_str: indices_str = "Aucun indice global."

    subtests_str = ""
    s_map = {
        "Similitudes": sim, "Vocabulaire": voc, "Information": info, "Compréhension": comp,
        "Cubes": cub, "Puzzles": puz, "Matrices": mat, "Balances": bal, "Arithmétique": arit,
        "Mém. Chiffres": mem_c, "Mém. Images": mem_i, "Séquence L-C": seq,
        "Code": cod, "Symboles": sym, "Barrage": bar
    }
    for name, score in s_map.items():
        if score > 0: subtests_str += f"- {name}: {score} (M=10, ET=3)\n"
    if not subtests_str: subtests_str = "Aucun subtest."

    with st.spinner(f"Analyse en cours avec {selected_model_name}..."):
        try:
            # ON UTILISE LE MODELE CHOISI DANS LA SIDEBAR
            model = genai.GenerativeModel(selected_model_name)
            
            prompt = f"""
            Rôle : Psychologue expert WISC-V.
            Tâche : Rédiger l'analyse psychométrique (Partie III).
            
            BIBLIOTHÈQUE DE RÉFÉRENCE (Documents fournis) :
            {knowledge_base}
            
            DONNÉES PATIENT :
            - Contexte : {anamnese}
            - Observations : {observations}
            - INDICES : {indices_str}
            - SUBTESTS : {subtests_str}
            
            CONSIGNES :
            1. Analyse UNIQUEMENT les scores présents.
            2. Utilise les documents fournis pour justifier les hypothèses.
            3. Situe les scores en Ecarts-Types.
            4. Synthétise forces/faiblesses et valide ou non l'homogénéité.
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            
        except Exception as e:
            st.error(f"Erreur avec ce modèle : {e}")
            st.info("Essayez de sélectionner un autre modèle dans la liste à gauche (ex: gemini-pro ou gemini-1.5-flash-001).")
