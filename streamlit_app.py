import streamlit as st
import google.generativeai as genai
import os
import io
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO
from pypdf import PdfReader
from docx import Document
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Assistant WISC-V", page_icon="🧠", layout="wide")
st.title("🧠 Assistant d'Analyse Expert en WISC V")

# --- AVERTISSEMENT ---
st.warning("⚠️ **AVERTISSEMENT :** Outil d'aide à la rédaction. L'analyse clinique reste la responsabilité du psychologue.")

# --- CONNEXION ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- FONCTIONS ---
def calculer_age(d_naiss, d_bilan):
    try:
        if d_bilan < d_naiss: return 0, 0
        ans = d_bilan.year - d_naiss.year
        mois = d_bilan.month - d_naiss.month
        if d_bilan.day < d_naiss.day: mois -= 1
        if mois < 0: ans -= 1; mois += 12
        return ans, mois
    except: return 0, 0

def check_homogeneite_indice(val1, val2, nom_indice):
    if val1 == 0 or val2 == 0: return None, ""
    ecart = abs(val1 - val2)
    if ecart >= 5: return False, f"⚠️ {nom_indice} Hétérogène (Écart {ecart})"
    else: return True, f"✅ {nom_indice} Homogène"

def plot_radar_chart(indices_dict):
    labels = list(indices_dict.keys())
    values = list(indices_dict.values())
    if sum(values) == 0: return None
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='#1f77b4', alpha=0.25)
    ax.plot(angles, values, color='#1f77b4', linewidth=2, label='Enfant')
    ax.plot(np.linspace(0, 2*np.pi, 100), [100]*100, color='red', linestyle='--', linewidth=1, label='Norme (100)')
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(40, 160)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize='small')
    return fig

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

def create_docx(text_content, prenom, age_str):
    doc = Document()
    doc.add_heading(f'Compte Rendu WISC-V : {prenom}', 0)
    doc.add_paragraph(f"Âge au bilan : {age_str}")
    p = doc.add_paragraph()
    runner = p.add_run("AVERTISSEMENT : Ce document est une base de travail. L'analyse clinique relève de la responsabilité du psychologue signataire.")
    runner.bold = True; runner.italic = True
    doc.add_paragraph(text_content)
    bio = io.BytesIO()
    doc.save(bio)
    return bio

# --- SIDEBAR (AUTOMATIQUE) ---
knowledge_base = ""
total_chars = 0
LIMIT_CHARS = 1000000 # Marge large pour Gemini 2.5/1.5

with st.sidebar:
    st.header("📚 Bibliothèque (Auto)")
    
    # Scan automatique du dossier
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    if local_files:
        # Barre de progression ou indicateur simple
        with st.spinner("Chargement des sources..."):
            for f in local_files:
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
                total_chars += len(c)
        
        # Affichage du statut
        st.success(f"✅ **{len(local_files)} documents intégrés**")
        
        # Petit détail repliable si tu veux vérifier ce
