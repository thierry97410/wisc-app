import streamlit as st
import google.generativeai as genai
import os
import io
from io import StringIO
from pypdf import PdfReader
from docx import Document # L'outil pour Word

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Pro", page_icon="📝", layout="wide")
st.title("🧠 Assistant WISC-V : Analyse & Export")

# --- CONNEXION ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- LECTURE ---
def read_file(file_obj, filename):
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

# --- FONCTION EXPORT WORD ---
def create_docx(text_content):
    doc = Document()
    doc.add_heading('Analyse WISC-V', 0)
    # On ajoute le texte généré
    doc.add_paragraph(text_content)
    # On sauvegarde en mémoire (virtuelle)
    bio = io.BytesIO()
    doc.save(bio)
    return bio

# --- SIDEBAR (Gestion Poids) ---
knowledge_base = ""
total_chars = 0
LIMIT_CHARS = 800000

with st.sidebar:
    st.header("📚 Bibliothèque")
    st.caption("Gardez la jauge VERTE (Gemini 2.5 Flash).")
    
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    if local_files:
        for f in local_files:
            if st.checkbox(f"📄 {f}", value=False):
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
                total_chars += len(c)
    
    st.divider()
    st.markdown(f"**Poids : {total_chars} car.**")
    if total_chars > LIMIT_CHARS:
        st.error("🛑 Trop lourd !")
    elif total_chars > 0:
        st.success("✅ Poids OK")

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Scores")
    c1, c2 = st.columns(2)
    with c1:
        qit = st.number_input("QIT", 0, 160, 0)
        icv = st.number_input("ICV", 0, 160, 0)
        ivs = st.number_input("IVS", 0, 160, 0)
    with c2:
        irf = st.number_input("IRF", 0, 160, 0)
        imt = st.number_input("IMT", 0, 160, 0)
        ivt = st.number_input("IVT", 0, 160, 0)

    with st.expander("Subtests"):
        sc1, sc2 = st.columns(2)
        with sc1:
            sim = st.number_input("Similitudes", 0, 19, 0)
            voc = st.number_input("Vocabulaire", 0, 19, 0)
            info = st.number_input("Info", 0, 19, 0)
            comp = st.number_input("Comp", 0, 19, 0)
            cub = st.number_input("Cubes", 0, 19, 0)
            puz = st.number_input("Puzzles", 0, 19, 0)
        with sc2:
            mat = st.number_input("Matrices", 0, 19, 0)
            bal = st.number_input("Balances", 0, 19, 0)
            arit = st.number_input("Arithmétique", 0, 19, 0)
            memc = st.number_input("Mém. Chiffres", 0, 19, 0)
            memi = st.number_input("Mém. Images", 0, 19, 0)
            seq = st.number_input("Séquence", 0, 19, 0)
            cod = st.number_input("Code", 0, 19, 0)
            sym = st.number_input("Symboles", 0, 19, 0)
            bar = st.number_input("Barrage", 0, 19, 0)

with col2:
    st.subheader("2. Clinique")
    ana = st.text_area("Anamnèse", height=150)
    obs = st.text_area("Observations", height=150)

# --- GENERATION ---
if st.button("✨ Analyser (Gemini 2.5)", type="primary"):
    
    if total_chars > LIMIT_CHARS:
        st.error("Décochez des livres à gauche !")
        st.stop()

    data = "SCORES:\n"
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: data += f"- {k}: {v}\n"
    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    for k,v in sub_map.items():
        if v > 0: data += f"- {k}: {v}\n"

    with st.spinner("Rédaction en cours..."):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""Rôle: Expert WISC-V. SOURCES: {knowledge_base}. CAS: {ana} / {obs} / {data}. TÂCHE: Rédiger analyse psychométrique détaillée (Partie III). Justifier avec sources."""
            
            res = model.generate_content(prompt)
            
            # Affichage écran
            st.markdown("### Résultat :")
            st.markdown(res.text)
            
            # Création du bouton Word
            docx_file = create_docx(res.text)
            
            st.download_button(
                label="📄 Télécharger en Word (.docx)",
                data=docx_file,
                file_name="Analyse_WISC.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        except Exception as e:
            st.error(f"Erreur : {e}")
