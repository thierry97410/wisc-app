import streamlit as st
import google.generativeai as genai
import os
from io import StringIO
from pypdf import PdfReader

# --- CONFIGURATION ---
st.set_page_config(page_title="WISC-V Expert (Complet)", page_icon="🧠", layout="wide")
st.title("🧠 Assistant WISC-V : Expert & Documenté")

# --- CONNEXION API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Erreur : Clé API manquante dans les secrets.")
    st.stop()

# --- FONCTION DE LECTURE ---
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

# --- SIDEBAR : GESTION DES DOCS ---
knowledge_base = ""
with st.sidebar:
    st.header("📚 Documents de Référence")
    
    # Fichiers locaux
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    
    if local_files:
        st.info("Décochez des livres si vous avez une erreur de Quota.")
        for f in local_files:
            # Par défaut tout est coché
            if st.checkbox(f"📄 {f}", value=True):
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
    
    st.divider()
    # Upload manuel
    uploads = st.file_uploader("Ajout (+)", type=['pdf', 'txt'], accept_multiple_files=True)
    if uploads:
        for u in uploads:
            c = read_file(u, u.name)
            knowledge_base += f"\n--- UPLOAD: {u.name} ---\n{c}\n"

# --- INTERFACE PRINCIPALE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Scores & Indices")
    
    # Indices
    c1, c2 = st.columns(2)
    with c1:
        qit = st.number_input("QIT", 0, 160, 0)
        icv = st.number_input("ICV", 0, 160, 0)
        ivs = st.number_input("IVS", 0, 160, 0)
    with c2:
        irf = st.number_input("IRF", 0, 160, 0)
        imt = st.number_input("IMT", 0, 160, 0)
        ivt = st.number_input("IVT", 0, 160, 0)
    
    st.markdown("---")
    st.markdown("**2. Les 15 Subtests (Notes Standard)**")
    
    # Organisation par colonnes pour tout faire tenir
    sc1, sc2 = st.columns(2)
    with sc1:
        st.caption("Verbal & Visuel")
        sim = st.number_input("Similitudes", 0, 19, 0)
        voc = st.number_input("Vocabulaire", 0, 19, 0)
        info = st.number_input("Information (Opt)", 0, 19, 0)
        comp = st.number_input("Compréhension (Opt)", 0, 19, 0)
        cub = st.number_input("Cubes", 0, 19, 0)
        puz = st.number_input("Puzzles Visuels", 0, 19, 0)
        
    with sc2:
        st.caption("Raisonnement, Mémoire & Vitesse")
        mat = st.number_input("Matrices", 0, 19, 0)
        bal = st.number_input("Balances", 0, 19, 0)
        arit = st.number_input("Arithmétique (Opt)", 0, 19, 0)
        memc = st.number_input("Mém. Chiffres", 0, 19, 0)
        memi = st.number_input("Mém. Images", 0, 19, 0)
        seq = st.number_input("Séquence L-C (Opt)", 0, 19, 0)
        cod = st.number_input("Code", 0, 19, 0)
        sym = st.number_input("Symboles", 0, 19, 0)
        bar = st.number_input("Barrage (Opt)", 0, 19, 0)

with col2:
    st.subheader("3. Clinique")
    ana = st.text_area("Anamnèse & Motif", height=200, placeholder="Ex: Arthur, 9 ans...")
    obs = st.text_area("Observations pendant le test", height=200, placeholder="Ex: Fatigabilité, anxiété, impulsivité...")

# --- GENERATION ---
if st.button("✨ Lancer l'Analyse Complète", type="primary"):
    
    # 1. Formatage des indices
    indices_str = ""
    for k,v in {"QIT":qit,"ICV":icv,"IVS":ivs,"IRF":irf,"IMT":imt,"IVT":ivt}.items():
        if v > 0: indices_str += f"- Indice {k}: {v} (M=100, ET=15)\n"
    if not indices_str: indices_str = "Aucun indice global calculé."

    # 2. Formatage des 15 subtests
    sub_map = {
        "Similitudes":sim, "Vocabulaire":voc, "Information":info, "Compréhension":comp,
        "Cubes":cub, "Puzzles":puz, 
        "Matrices":mat, "Balances":bal, "Arithmétique":arit,
        "Mém. Chiffres":memc, "Mém. Images":memi, "Séquence L-C":seq,
        "Code":cod, "Symboles":sym, "Barrage":bar
    }
    subtests_str = ""
    for k,v in sub_map.items():
        if v > 0: subtests_str += f"- {k}: {v} (M=10, ET=3)\n"
    if not subtests_str: subtests_str = "Aucun subtest saisi."

    with st.spinner("Analyse experte en cours..."):
        try:
            # Modèle Flash pour la robustesse
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Tu es un psychologue clinicien expert du WISC-V.
            
            ### DOCUMENTS DE RÉFÉRENCE (Analyse théorique obligatoire) :
            {knowledge_base}
            
            ### DONNÉES DU PATIENT :
            - Anamnèse : {ana}
            - Observations : {obs}
            
            ### SCORES :
            {indices_str}
            
            ### DÉTAIL DES SUBTESTS :
            {subtests_str}
            
            ### CONSIGNE DE RÉDACTION :
            Rédige la partie "III. Évaluation Psychométrique" du bilan.
            1. **Intégration** : Ne cite pas les scores sans les expliquer. Relie les chiffres aux observations (ex: "Le score faible en Barrage (7) confirme la lenteur graphomotrice observée...").
            2. **Théorie** : Utilise les documents fournis pour étayer tes hypothèses (CHC, Facteur g, etc.).
            3. **Statistiques** : Mentionne les Ecarts-Types pour situer l'enfant.
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
            st.warning("Astuce : Si c'est une erreur de quota (429), décochez un livre dans la barre de gauche.")
