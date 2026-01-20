import streamlit as st
import google.generativeai as genai
import os
import io
from io import StringIO
from pypdf import PdfReader
from docx import Document
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Expert Pro", page_icon="🧠", layout="wide")
st.title("🧠 Assistant WISC-V : Expert & Indices Complémentaires")

# --- CONNEXION ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante.")
    st.stop()

# --- FONCTION CALCUL AGE ---
def calculer_age(d_naiss, d_bilan):
    if d_bilan < d_naiss: return 0, 0
    ans = d_bilan.year - d_naiss.year
    mois = d_bilan.month - d_naiss.month
    if d_bilan.day < d_naiss.day: mois -= 1
    if mois < 0:
        ans -= 1
        mois += 12
    return ans, mois

# --- FONCTION LECTURE ---
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

# --- EXPORT WORD ---
def create_docx(text_content, prenom, age_str):
    doc = Document()
    doc.add_heading(f'Analyse WISC-V : {prenom}', 0)
    doc.add_paragraph(f"Âge : {age_str}")
    doc.add_paragraph(text_content)
    bio = io.BytesIO()
    doc.save(bio)
    return bio

# --- SIDEBAR (Gestion Poids) ---
knowledge_base = ""
total_chars = 0
LIMIT_CHARS = 800000

with st.sidebar:
    st.header("📚 Bibliothèque")
    st.caption("Cochez uniquement le Manuel d'Interprétation.")
    
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    if local_files:
        for f in local_files:
            if st.checkbox(f"📄 {f}", value=False):
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
                total_chars += len(c)
    
    st.divider()
    if total_chars > LIMIT_CHARS: st.error("🛑 Trop lourd !")
    elif total_chars > 0: st.success("✅ Poids OK")

# --- INTERFACE ---
st.subheader("1. Identité")
c1, c2, c3 = st.columns(3)
with c1:
    prenom = st.text_input("Prénom", placeholder="Ex: Léo")
    sexe = st.radio("Sexe", ["Garçon", "Fille"], horizontal=True)
with c2:
    d_naiss = st.date_input("Né(e) le", value=date(2015, 1, 1), min_value=date(1900,1,1))
    lateralite = st.radio("Latéralité", ["Droitier", "Gaucher"], horizontal=True)
with c3:
    d_test = st.date_input("Date Bilan", value=date.today())
    ans, mois = calculer_age(d_naiss, d_test)
    st.markdown(f"### {ans} ans {mois} mois")

st.divider()

col_scores, col_inputs = st.columns([1, 1])

with col_scores:
    st.subheader("2. Saisie des Subtests (Notes Standard)")
    # Saisie directe pour calcul live
    sc1, sc2 = st.columns(2)
    with sc1:
        sim = st.number_input("Similitudes", 0, 19, 0)
        voc = st.number_input("Vocabulaire", 0, 19, 0)
        cub = st.number_input("Cubes", 0, 19, 0)
        mat = st.number_input("Matrices", 0, 19, 0)
        bal = st.number_input("Balances", 0, 19, 0)
        arit = st.number_input("Arithmétique", 0, 19, 0)
        cod = st.number_input("Code", 0, 19, 0)
    with sc2:
        info = st.number_input("Information", 0, 19, 0)
        comp = st.number_input("Compréhension", 0, 19, 0)
        puz = st.number_input("Puzzles", 0, 19, 0)
        memc = st.number_input("Mém. Chiffres", 0, 19, 0)
        memi = st.number_input("Mém. Images", 0, 19, 0)
        sym = st.number_input("Symboles", 0, 19, 0)
        seq = st.number_input("Séquence L-C", 0, 19, 0)
        bar = st.number_input("Barrage", 0, 19, 0)

with col_inputs:
    st.subheader("3. Indices Principaux & Complémentaires")
    
    # CALCUL AUTOMATIQUE DES SOMMES POUR AIDE
    somme_iag = sim + voc + cub + mat + bal
    somme_icc = memc + memi + sym + cod
    # INV = Cubes + Puzzles + Matrices + Balances + Mém Images + Code
    somme_inv = cub + puz + mat + bal + memi + cod
    
    st.info(f"💡 **Sommes calculées (Regarde tes tables) :**\n- Pour IAG : **{somme_iag}**\n- Pour ICC : **{somme_icc}**\n- Pour INV : **{somme_inv}**")
    
    ic1, ic2 = st.columns(2)
    with ic1:
        qit = st.number_input("QIT (Total)", 0, 160, 0)
        icv = st.number_input("ICV (Verbal)", 0, 160, 0)
        ivs = st.number_input("IVS (Visuel)", 0, 160, 0)
        irf = st.number_input("IRF (Fluide)", 0, 160, 0)
    with ic2:
        imt = st.number_input("IMT (Mémoire)", 0, 160, 0)
        ivt = st.number_input("IVT (Vitesse)", 0, 160, 0)
        st.markdown("---")
        # Indices complémentaires
        iag = st.number_input("IAG (Aptitude G.)", 0, 160, 0)
        icc = st.number_input("ICC (Comp. Cogn.)", 0, 160, 0)
        inv = st.number_input("INV (Non Verbal)", 0, 160, 0)

st.divider()
st.subheader("4. Clinique")
ana = st.text_area("Anamnèse", height=100)
obs = st.text_area("Observations", height=100)

# --- GENERATION ---
if st.button(f"✨ Analyser le profil de {prenom if prenom else 'l\'enfant'}", type="primary"):
    
    if total_chars > LIMIT_CHARS: st.error("Trop lourd !"); st.stop()

    infos = f"Enfant: {prenom}, {sexe}. {ans} ans {mois} mois. Latéralité: {lateralite}."
    
    data = "SCORES:\n"
    # Indices
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: data += f"- Indice {k}: {v}\n"
    for k,v in {"IAG":iag, "ICC":icc, "INV (Non Verbal)":inv}.items():
        if v > 0: data += f"- Indice Complémentaire {k}: {v}\n"
        
    sub_map = {"Sim":sim, "Voc":voc, "Info":info, "Comp":comp, "Cub":cub, "Puz":puz, "Mat":mat, "Bal":bal, "Arit":arit, "MemC":memc, "MemI":memi, "Seq":seq, "Cod":cod, "Sym":sym, "Bar":bar}
    for k,v in sub_map.items():
        if v > 0: data += f"- {k}: {v}\n"

    with st.spinner(f"Rédaction experte en cours..."):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Rôle: Expert WISC-V.
            CONTEXTE: {infos}
            ANAMNÈSE: {ana}
            OBSERVATIONS: {obs}
            RÉSULTATS:
            {data}
            SOURCES: {knowledge_base}
            
            CONSIGNE DE RÉDACTION (Partie Interprétation):
            1. Analyse l'homogénéité du QIT.
            
            2. FOCUS SUR LES INDICES COMPLÉMENTAIRES (Si fournis) :
               - IAG vs ICC : Vérifie si le potentiel de raisonnement (IAG) est masqué par les fragilités instrumentales (ICC).
               - ANALYSE INV : Si l'INV est fourni ({inv}), compare-le à l'ICV. Si l'ICV est faible (ou trouble du langage), souligne que l'INV est une mesure plus fiable de l'intelligence fluide.
               
            3. CROISEMENT CLINIQUE :
               - Lie les chutes de scores aux observations (ex: anxiété, agitation, problème moteur si gaucher + échec Code).
               
            Utilise un ton professionnel et bienveillant.
            """
            
            res = model.generate_content(prompt)
            st.markdown("### Résultat :")
            st.markdown(res.text)
            
            filename = f"Analyse_{prenom}_{ans}ans.docx" if prenom else "Analyse.docx"
            docx_file = create_docx(res.text, prenom, f"{ans} ans {mois} mois")
            st.download_button("📄 Télécharger Word", docx_file, filename, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
        except Exception as e: st.error(f"Erreur : {e}")
