import streamlit as st
import google.generativeai as genai
from io import StringIO

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="WISC-V Expert + Bibliothèque", page_icon="📚", layout="wide")

# --- TITRE ---
st.title("🧠 WISC-V Expert : Analyse Clinique & Théorique")
st.markdown("""
Ce système croise les **scores chiffrés**, **l'anamnèse** et vos **documents de référence** pour produire une analyse de très haute précision.
""")

# --- CONFIGURATION API ---
# Si vous utilisez gemini-1.5-flash, c'est gratuit et ça permet de lire des livres entiers
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur de clé API. Vérifiez vos Secrets.")
    st.stop()

# --- BARRE LATÉRALE : BIBLIOTHÈQUE ---
with st.sidebar:
    st.header("📚 Base de Connaissances")
    st.info("Déposez ici vos manuels et guides (.txt) pour que l'IA s'appuie dessus.")
    uploaded_files = st.file_uploader(
        "Charger les documents de référence", 
        type=['txt'], 
        accept_multiple_files=True
    )
    
    knowledge_base = ""
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Lecture des fichiers textes
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            file_content = stringio.read()
            knowledge_base += f"\n--- DOCUMENT : {uploaded_file.name} ---\n{file_content}\n"
        st.success(f"{len(uploaded_files)} documents intégrés à l'analyse !")
    else:
        st.warning("Aucun document de référence chargé. L'IA utilisera ses connaissances générales.")

# --- INTERFACE PRINCIPALE ---
col_gauche, col_droite = st.columns([1, 1])

with col_gauche:
    st.subheader("1. Les Scores (WISC-V)")
    
    # Indices
    c1, c2 = st.columns(2)
    with c1:
        qit = st.number_input("QIT Total", value=100)
        icv = st.number_input("ICV (Verbal)", value=100)
        ivs = st.number_input("IVS (Visuospatial)", value=100)
    with c2:
        irf = st.number_input("IRF (Fluide)", value=100)
        imt = st.number_input("IMT (Mémoire)", value=100)
        ivt = st.number_input("IVT (Vitesse)", value=100)

    st.markdown("---")
    
    # Subtests
    with st.expander("📝 Détail des Subtests (Notes Standard)", expanded=False):
        st.caption("Moyenne = 10, Ecart-type = 3")
        sc1, sc2 = st.columns(2)
        with sc1:
            similitudes = st.number_input("Similitudes", 10)
            vocabulaire = st.number_input("Vocabulaire", 10)
            cubes = st.number_input("Cubes", 10)
            puzzles = st.number_input("Puzzles", 10)
        with sc2:
            matrices = st.number_input("Matrices", 10)
            balances = st.number_input("Balances", 10)
            mem_chiffres = st.number_input("Mém. Chiffres", 10)
            code = st.number_input("Code", 10)

with col_droite:
    st.subheader("2. Clinique & Observations")
    anamnese = st.text_area("Contexte / Anamnèse", height=150, placeholder="Motif, histoire du patient...")
    observations = st.text_area("Observations pendant le test", height=150, placeholder="Comportement, fatigue, anxiété, stratégies...")

# --- GÉNÉRATION ---
st.markdown("---")
if st.button("✨ Lancer l'Analyse Croisée", type="primary"):
    with st.spinner("L'IA consulte vos manuels et analyse les données..."):
        try:
            # On utilise le modèle Flash pour sa grande capacité de lecture (Context Window)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Tu es un expert en évaluation psychologique de l'enfant.
            Ta mission est de rédiger la partie "Évaluation Psychométrique" d'un compte-rendu WISC-V.
            
            ### SOURCE DE CONNAISSANCES (IMPORTANT)
            Tu dois t'appuyer sur le contenu des documents suivants fournis par l'utilisateur pour justifier tes analyses, 
            notamment concernant les écarts-types, les divergences inter-indices et les hypothèses cliniques :
            
            {knowledge_base}
            
            ### DONNÉES CLINIQUES DU PATIENT
            - Contexte : {anamnese}
            - Observations : {observations}
            
            ### SCORES DU PATIENT
            - INDICES (M=100, ET=15) : QIT={qit}, ICV={icv}, IVS={ivs}, IRF={irf}, IMT={imt}, IVT={ivt}
            - SUBTESTS CLÉS : Similitudes={similitudes}, Vocabulaire={vocabulaire}, Cubes={cubes}, Puzzles={puzzles}, Matrices={matrices}, Balances={balances}, Mém. Chiffres={mem_chiffres}, Code={code}
            
            ### CONSIGNES DE RÉDACTION
            1. **Rigueur Statistique** : Utilise le vocabulaire des manuels fournis (ex: "Zone Moyenne", "Supérieur", etc.) et cite les écarts-types précis.
            2. **Analyse Intégrative** : Ne fais pas que décrire les scores. Croise le score avec l'observation (ex: "La chute en Code s'explique par l'anxiété observée...").
            3. **Références** : Si pertinent, fais référence implicitement aux principes théoriques des documents fournis (ex: modèle CHC, saturation facteur g, etc. si mentionnés dans les textes).
            4. **Structure** : Paragraphes fluides, ton professionnel.
            """
            
            response = model.generate_content(prompt)
            st.success("Analyse terminée basées sur vos documents !")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
