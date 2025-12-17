import streamlit as st
import google.generativeai as genai
import os
from io import StringIO, BytesIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Auto-Expert (PDF+TXT)", page_icon="🧠", layout="wide")
st.title("🧠 Assistant WISC-V : Expert & Documenté")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- FONCTION DE LECTURE UNIVERSELLE ---
def read_file_content(file_obj, filename):
    """Lit le texte d'un fichier, qu'il soit PDF ou TXT."""
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            # Lecture PDF
            pdf_reader = PdfReader(file_obj)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        else:
            # Lecture TXT (par défaut)
            # Si c'est un fichier uploadé (BytesIO), on décode. Si c'est un fichier local (str), on lit.
            if isinstance(file_obj, str): # Chemin local
                with open(file_obj, "r", encoding="utf-8") as f:
                    text = f.read()
            else: # Fichier uploadé via Streamlit
                stringio = StringIO(file_obj.getvalue().decode("utf-8"))
                text = stringio.read()
    except Exception as e:
        st.error(f"Erreur de lecture sur {filename}: {e}")
    return text

# --- CHARGEMENT AUTOMATIQUE (Serveur) ---
knowledge_base = ""
files_loaded = []

# Scanne le dossier pour trouver .txt ET .pdf
for filename in os.listdir('.'):
    if filename.lower().endswith(('.txt', '.pdf')):
        # On ignore les fichiers systèmes ou le script lui-même
        if filename == "requirements.txt" or filename == "app.py":
            continue
            
        content = read_file_content(filename, filename)
        if content:
            knowledge_base += f"\n--- REFERENCE : {filename} ---\n{content}\n"
            files_loaded.append(filename)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("📚 Bibliothèque")
    
    if files_loaded:
        st.success(f"✅ {len(files_loaded)} documents chargés automatiquement.")
        with st.expander("Voir la liste"):
            for f in files_loaded:
                icon = "📕" if f.endswith('.pdf') else "📄"
                st.markdown(f"{icon} *{f}*")
    else:
        st.info("Aucun document (PDF/TXT) trouvé sur le serveur.")

    st.markdown("---")
    st.markdown("**Ajout manuel :**")
    uploaded_files = st.file_uploader(
        "Charger d'autres documents", 
        type=['txt', 'pdf'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for u_file in uploaded_files:
            content = read_file_content(u_file, u_file.name)
            if content:
                knowledge_base += f"\n--- REFERENCE SUPPLEMENTAIRE : {u_file.name} ---\n{content}\n"
        st.success("Documents supplémentaires ajoutés !")

# --- INTERFACE PRINCIPALE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Données Chiffrées")
    c1, c2 = st.columns(2)
    with c1:
        qit = st.number_input("QIT", 100)
        icv = st.number_input("ICV", 100)
        ivs = st.number_input("IVS", 100)
    with c2:
        irf = st.number_input("IRF", 100)
        imt = st.number_input("IMT", 100)
        ivt = st.number_input("IVT", 100)
    
    with st.expander("Détail des Subtests (Notes Standard)", expanded=False):
        sc1, sc2 = st.columns(2)
        with sc1:
            sim = st.number_input("Similitudes", 10)
            voc = st.number_input("Vocabulaire", 10)
            cub = st.number_input("Cubes", 10)
            puz = st.number_input("Puzzles", 10)
        with sc2:
            mat = st.number_input("Matrices", 10)
            bal = st.number_input("Balances", 10)
            mem = st.number_input("Mém. Chiffres", 10)
            cod = st.number_input("Code", 10)

with col2:
    st.subheader("2. Clinique")
    anamnese = st.text_area("Contexte", height=150, placeholder="Histoire, motif...")
    observations = st.text_area("Observations", height=150, placeholder="Comportement...")

if st.button("✨ Lancer l'Analyse Expert", type="primary"):
    with st.spinner("Lecture des documents (PDF/TXT) et analyse..."):
        # Modèle Flash obligatoire pour gérer le volume de texte des PDF
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Rôle : Psychologue expert WISC-V.
        Tâche : Rédiger l'analyse psychométrique (Partie III).
        
        BIBLIOTHÈQUE DE RÉFÉRENCE (à utiliser pour justifier l'analyse) :
        {knowledge_base}
        
        CAS CLINIQUE :
        - Contexte : {anamnese}
        - Obs : {observations}
        - Scores Indices (M=100, ET=15) : QIT={qit}, ICV={icv}, IVS={ivs}, IRF={irf}, IMT={imt}, IVT={ivt}
        - Scores Subtests (M=10, ET=3) : Sim={sim}, Voc={voc}, Cub={cub}, Puz={puz}, Mat={mat}, Bal={bal}, Mem={mem}, Cod={cod}
        
        CONSIGNES :
        1. Utilise EXPLICITEMENT les connaissances extraites des PDF/TXT fournis (théorie, normes, interprétation).
        2. Fais des liens entre les scores et la clinique.
        3. Cite les écarts-types.
        4. Si des contradictions apparaissent (ex: QIT non valide), explique-les selon les manuels fournis.
        """
        
        try:
            res = model.generate_content(prompt)
            st.markdown(res.text)
        except Exception as e:
            st.error(f"Erreur : {e}")
