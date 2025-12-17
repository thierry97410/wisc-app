import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Assistant WISC-V Pro",
    page_icon="🧠",
    layout="wide"
)

# --- TITRE ET INTRODUCTION ---
st.title("🧠 Assistant de Rédaction WISC-V")
st.markdown("""
Cet outil génère une analyse psychométrique détaillée en croisant les scores chiffrés 
avec l'anamnèse et les observations cliniques.
""")

# --- CONFIGURATION API (Via st.secrets) ---
# Assurez-vous d'avoir configuré votre clé API dans les secrets Streamlit
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur : Clé API Google non trouvée. Veuillez la configurer dans les secrets Streamlit.")
    st.stop()

# --- COLONNES POUR L'INTERFACE ---
col_gauche, col_droite = st.columns([1, 2])

# --- 1. SAISIE DES SCORES (COLONNE GAUCHE) ---
with col_gauche:
    st.header("1. Les Scores")
    st.info("Moyenne = 100, Écart-Type = 15")
    
    qit = st.number_input("QIT (Quotient Intellectuel Total)", min_value=40, max_value=160, value=100)
    icv = st.number_input("ICV (Compréhension Verbale)", min_value=40, max_value=160, value=100)
    ivs = st.number_input("IVS (Visuospatial)", min_value=40, max_value=160, value=100)
    irf = st.number_input("IRF (Raisonnement Fluide)", min_value=40, max_value=160, value=100)
    imt = st.number_input("IMT (Mémoire de Travail)", min_value=40, max_value=160, value=100)
    ivt = st.number_input("IVT (Vitesse de Traitement)", min_value=40, max_value=160, value=100)

# --- 2. SAISIE CLINIQUE (COLONNE DROITE) ---
with col_droite:
    st.header("2. Contexte & Clinique")
    
    anamnese = st.text_area(
        "Contexte & Anamnèse",
        height=150,
        placeholder="Ex: Enfant de 8 ans, suspicion TDAH. Parents décrivent un enfant rêveur. Retard de langage..."
    )
    
    observations = st.text_area(
        "Observations pendant la passation",
        height=150,
        placeholder="Ex: Bonne collaboration mais fatigabilité. Impulsivité sur les tâches chronométrées. Anxiété de performance..."
    )

# --- 3. BOUTON ET GÉNÉRATION ---
st.markdown("---")
if st.button("✨ Générer l'Analyse Psychométrique", type="primary"):
    if not anamnese or not observations:
        st.warning("Attention : Pour une analyse pertinente, il est recommandé de remplir l'anamnèse et les observations.")
    
    with st.spinner("L'IA analyse les données et rédige le compte-rendu..."):
        try:
            # Création du modèle
            model = genai.GenerativeModel('gemini-pro')
            
            # Construction du prompt structuré
            prompt_complet = f"""
            Tu agis en tant que psychologue clinicien expert spécialisé dans l'évaluation cognitive (WISC-V).
            Ta tâche est de rédiger la partie "III. Évaluation Psychométrique" d'un bilan, en croisant les scores avec la clinique.

            ### DONNÉES DU PATIENT :
            - CONTEXTE/ANAMNÈSE : {anamnese}
            - OBSERVATIONS CLINIQUES : {observations}
            - SCORES : QIT={qit}, ICV={icv}, IVS={ivs}, IRF={irf}, IMT={imt}, IVT={ivt}

            ### CONSIGNES DE RÉDACTION STRICTES :
            
            1. ANALYSE STATISTIQUE ET ÉCARTS-TYPES :
               Pour chaque indice, tu dois situer le score par rapport à la moyenne (100) en termes d'Écarts-Types (ET=15).
               - Ex: "Avec 130, l'ICV se situe à deux écarts-types au-dessus de la moyenne."
            
            2. SYNTHÈSE CLINIQUE (TRIANGULATION) :
               Ne fais pas une simple lecture de chiffres. Explique les scores par le comportement :
               - Si un score est faible, cherche la cause dans les OBSERVATIONS (ex: anxiété, inattention).
               - Si le profil est hétérogène, explique pourquoi le QIT n'est pas représentatif.
            
            3. FORME :
               - Rédige des paragraphes fluides (pas de listes à puces excessives).
               - Ton professionnel et nuancé.
               - Structure : Analyse par Indice puis Synthèse globale.
            """
            
            # Appel à l'IA
            response = model.generate_content(prompt_complet)
            
            # Affichage du résultat
            st.success("Analyse générée avec succès !")
            st.markdown("### 📝 Proposition de rédaction")
            st.markdown(response.text)
            
            # Bouton de copie (astuce visuelle)
            st.info("Vous pouvez copier le texte ci-dessus et le coller dans votre rapport Word.")

        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")
