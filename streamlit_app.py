import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="WISC-V Expert", page_icon="🧠", layout="wide")

# --- TITRE ---
st.title("🧠 Assistant de Rédaction WISC-V (Complet)")
st.markdown("Analyse croisée : Scores + Subtests + Clinique")

# --- CONFIGURATION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur de clé API. Vérifiez vos Secrets.")
    st.stop()

# --- INTERFACE ---
col_gauche, col_droite = st.columns([1, 1])

with col_gauche:
    st.subheader("1. Les Indices (Notes Composites)")
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
    st.subheader("2. Les Subtests (Notes Standard)")
    st.caption("Laissez à 10 si non administré.")
    
    with st.expander("📝 Saisir les Subtests (Cubes, Similitudes...)", expanded=True):
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("**Compréhension Verbale**")
            similitudes = st.number_input("Similitudes", value=10, min_value=1, max_value=19)
            vocabulaire = st.number_input("Vocabulaire", value=10, min_value=1, max_value=19)
            information = st.number_input("Information (Opt)", value=10, min_value=1, max_value=19)
            comprehension = st.number_input("Compréhension (Opt)", value=10, min_value=1, max_value=19)
            
            st.markdown("**Visuospatial**")
            cubes = st.number_input("Cubes", value=10, min_value=1, max_value=19)
            puzzles = st.number_input("Puzzles Visuels", value=10, min_value=1, max_value=19)

        with sc2:
            st.markdown("**Raisonnement Fluide**")
            matrices = st.number_input("Matrices", value=10, min_value=1, max_value=19)
            balances = st.number_input("Balances", value=10, min_value=1, max_value=19)
            
            st.markdown("**Mémoire de Travail**")
            mem_chiffres = st.number_input("Mém. Chiffres", value=10, min_value=1, max_value=19)
            mem_images = st.number_input("Mém. Images", value=10, min_value=1, max_value=19)
            
            st.markdown("**Vitesse de Traitement**")
            code = st.number_input("Code", value=10, min_value=1, max_value=19)
            symboles = st.number_input("Symboles", value=10, min_value=1, max_value=19)

with col_droite:
    st.subheader("3. Contexte & Clinique")
    anamnese = st.text_area("Contexte / Anamnèse", height=200, placeholder="Motif, histoire scolaire, développement...")
    observations = st.text_area("Observations / Comportement", height=200, placeholder="Attitude, anxiété, méthode de travail, fatigue...")

# --- GENERATION ---
st.markdown("---")
if st.button("✨ Générer l'Analyse Expert", type="primary"):
    with st.spinner("Analyse approfondie en cours..."):
        try:
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            Tu es un psychologue expert. Rédige la partie "Évaluation Psychométrique" du bilan.
            
            DONNÉES:
            - Contexte: {anamnese}
            - Observations: {observations}
            
            SCORES INDICES (M=100, ET=15):
            - QIT={qit}, ICV={icv}, IVS={ivs}, IRF={irf}, IMT={imt}, IVT={ivt}
            
            SCORES SUBTESTS (M=10, ET=3):
            - Verbal: Similitudes={similitudes}, Vocabulaire={vocabulaire}, Info={information}, Compr={comprehension}
            - Visuo: Cubes={cubes}, Puzzles={puzzles}
            - Fluide: Matrices={matrices}, Balances={balances}
            - Mémoire: Chiffres={mem_chiffres}, Images={mem_images}
            - Vitesse: Code={code}, Symboles={symboles}

            CONSIGNES EXPERTES :
            1. ANALYSE STATISTIQUE : Pour chaque Indice, cite l'écart-type (ex: "ICV à +2 ET de la moyenne").
            2. ANALYSE INTRA-INDIVIDUELLE : Regarde les subtests ! Si Cubes est fort (16) mais Puzzles faible (8), relève cette dissociation.
            3. TRIANGULATION : Explique les chiffres par l'observation (ex: chute en Code liée au perfectionnisme observé).
            4. STYLE : Professionnel, fluide, structuré par domaine.
            """
            
            response = model.generate_content(prompt)
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Erreur : {e}")
