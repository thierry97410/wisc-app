import streamlit as st
import google.generativeai as genai
import os

st.title("🕵️ Diagnostic de Connexion (France)")

# 1. Test de la Clé
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    # On masque la clé sauf les 4 derniers caractères pour vérifier
    masked_key = "..." + api_key[-4:]
    st.success(f"✅ Clé API détectée : {masked_key}")
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Problème avec la clé API dans les secrets : {e}")
    st.stop()

# 2. Test des Modèles Disponibles
st.subheader("Modèles accessibles avec cette clé :")

try:
    models = genai.list_models()
    found_flash = False
    
    model_list = []
    for m in models:
        # On ne garde que les modèles qui savent générer du texte
        if 'generateContent' in m.supported_generation_methods:
            model_list.append(m.name)
            st.write(f"- `{m.name}`")
            if "flash" in m.name:
                found_flash = True

    if not model_list:
        st.error("⚠️ La connexion fonctionne, mais AUCUN modèle n'est retourné. La clé est peut-être restreinte.")
    elif found_flash:
        st.success("🎉 VICTOIRE ! Le modèle 'Flash' est bien disponible. C'était juste une erreur de nom ou de version.")
    else:
        st.warning("⚠️ Des modèles sont trouvés, mais pas le 'Flash'. Nous devrons utiliser 'gemini-pro'.")

except Exception as e:
    st.error(f"❌ Erreur critique lors de la connexion à Google : {e}")
    st.info("Conseil : Vérifiez que vous avez bien fait 'Reboot App' après avoir changé le fichier requirements.txt")

# 3. Test de Génération (Preuve finale)
if st.button("Lancer un test de génération (Bonjour)"):
    # On essaie le meilleur modèle trouvé
    target_model = 'gemini-1.5-flash' if found_flash else 'gemini-pro'
    try:
        model = genai.GenerativeModel(target_model)
        response = model.generate_content("Dis bonjour depuis la France !")
        st.balloons()
        st.markdown(f"### 🤖 Réponse de {target_model} :\n{response.text}")
    except Exception as e:
        st.error(f"Erreur lors de la génération : {e}")
