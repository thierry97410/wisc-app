import streamlit as st
import google.generativeai as genai

st.title("🕵️ Scanner de Modèles (Diagnostic)")

# 1. Configuration
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    st.success("✅ Clé API connectée.")
except Exception as e:
    st.error(f"❌ Erreur Clé API : {e}")
    st.stop()

# 2. Scan des modèles
st.subheader("Liste des modèles disponibles pour vous :")

found_models = []

try:
    # On demande à Google la liste brute
    for m in genai.list_models():
        # On affiche tout ce qui peut générer du texte
        if 'generateContent' in m.supported_generation_methods:
            st.code(f"Nom exact : {m.name}")
            found_models.append(m.name)
            
    if not found_models:
        st.error("⚠️ Aucun modèle trouvé ! Votre clé est probablement bridée géographiquement.")
    else:
        st.balloons()
        st.success("Copiez le nom d'un modèle ci-dessus (ex: models/gemini-1.5-flash) et donnez-le moi !")

except Exception as e:
    st.error(f"Erreur de connexion : {e}")
