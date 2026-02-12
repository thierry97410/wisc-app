import streamlit as st
import google.generativeai as genai
import os
import io
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO
from pypdf import PdfReader
from docx import Document
from datetime import date, datetime

# ==========================================
# 0. ADMINISTRATION
# ==========================================
RESTRICTION_ACTIVE = False
DATE_EXPIRATION = date(2025, 12, 31) 
MOT_DE_PASSE = "WISC-PRO"

# ==========================================
# 1. CONFIGURATION & SÉCURITÉ
# ==========================================
st.set_page_config(page_title="Assistant WISC-V", page_icon="🧠", layout="wide")

if RESTRICTION_ACTIVE:
    if date.today() > DATE_EXPIRATION:
        st.error("⛔ ACCÈS EXPIRÉ"); st.stop()
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 Connexion"); input_pass = st.text_input("Mot de passe :", type="password")
        if st.button("Valider"):
            if input_pass == MOT_DE_PASSE: st.session_state.authenticated = True; st.rerun()
            else: st.error("Erreur.")
        st.stop()

st.title("🧠 Assistant d'Analyse Expert en WISC V")
st.warning("⚠️ **AVERTISSEMENT :** Outil d'aide à la rédaction. L'analyse clinique reste la responsabilité du psychologue.")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Clé API manquante."); st.stop()

# --- GESTION DU RESET ---
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0

def reset_all():
    keys_to_clear = [
        'sim', 'voc', 'info', 'comp', 'cub', 'puz', 'mat', 'bal', 'arit', 
        'memc', 'memi', 'seq', 'cod', 'sym', 'bar',
        'qit', 'perc_qit', 'qit_bas', 'qit_haut',
        'icv', 'perc_icv', 'icv_bas', 'icv_haut',
        'ivs', 'perc_ivs', 'ivs_bas', 'ivs_haut',
        'irf', 'perc_irf', 'irf_bas', 'irf_haut',
        'imt', 'perc_imt', 'imt_bas', 'imt_haut',
        'ivt', 'perc_ivt', 'ivt_bas', 'ivt_haut',
        'iag', 'iag_bas', 'iag_haut',
        'icc', 'icc_bas', 'icc_haut',
        'inv', 'inv_bas', 'inv_haut',
        'import_status'
    ]
    for key in keys_to_clear:
        if key in st.session_state: del st.session_state[key]
    
    st.session_state['jn'] = 1; st.session_state['mn'] = 1; st.session_state['an'] = 2015
    st.session_state['jb'] = date.today().day; st.session_state['mb'] = date.today().month; st.session_state['ab'] = date.today().year
    st.session_state.uploader_key += 1
    st.rerun()

# --- INITIALISATION VARIABLES ---
vars_scores = [
    'sim', 'voc', 'info', 'comp', 'cub', 'puz', 'mat', 'bal', 'arit', 
    'memc', 'memi', 'seq', 'cod', 'sym', 'bar',
    'qit', 'perc_qit', 'qit_bas', 'qit_haut',
    'icv', 'perc_icv', 'icv_bas', 'icv_haut',
    'ivs', 'perc_ivs', 'ivs_bas', 'ivs_haut',
    'irf', 'perc_irf', 'irf_bas', 'irf_haut',
    'imt', 'perc_imt', 'imt_bas', 'imt_haut',
    'ivt', 'perc_ivt', 'ivt_bas', 'ivt_haut',
    'iag', 'iag_bas', 'iag_haut',
    'icc', 'icc_bas', 'icc_haut',
    'inv', 'inv_bas', 'inv_haut'
]
for var in vars_scores:
    if var not in st.session_state: st.session_state[var] = 0.0 if 'perc' in var else 0

# Dates par défaut
if 'jn' not in st.session_state: st.session_state['jn'] = 1
if 'mn' not in st.session_state: st.session_state['mn'] = 1
if 'an' not in st.session_state: st.session_state['an'] = 2015
if 'jb' not in st.session_state: st.session_state['jb'] = date.today().day
if 'mb' not in st.session_state: st.session_state['mb'] = date.today().month
if 'ab' not in st.session_state: st.session_state['ab'] = date.today().year

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
    if ecart >= 4: return False, f"⚠️ {nom_indice} Hétérogène (Écart {ecart})" 
    else: return True, f"✅ {nom_indice} Homogène"

def plot_radar_chart(indices_dict):
    labels = list(indices_dict.keys())
    values = list(indices_dict.values())
    if sum(values) == 0: return None
    values += values[:1]; angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist(); angles += angles[:1]
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='#1f77b4', alpha=0.25)
    ax.plot(angles, values, color='#1f77b4', linewidth=2, label='Enfant')
    ax.plot(np.linspace(0, 2*np.pi, 100), [100]*100, color='red', linestyle='--', linewidth=1, label='Norme (100)')
    ax.set_yticklabels([]); ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, fontsize=10); ax.set_ylim(40, 160)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize='small')
    return fig

def read_file(file_obj, filename):
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            pdf_reader = PdfReader(file_obj)
            for page in pdf_reader.pages: t = page.extract_text(); text += t + "\n" if t else ""
        else:
            stringio = StringIO(file_obj.getvalue().decode("utf-8")); text = stringio.read()
    except: pass
    return text

def extract_qglobal_data(text_content):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Extrais les données WISC-V du texte ci-dessous en JSON.
        IMPORTANT: Si une valeur est manquante, mets 0 (ou "" pour les dates).
        
        Variables Scores (Note Standard 1-19): sim, voc, info, comp, cub, puz, mat, bal, arit, memc, memi, seq, cod, sym, bar
        Indices (Note Composite): qit, icv, ivs, irf, imt, ivt, iag, icc, inv
        Percentiles: perc_qit, perc_icv, perc_ivs, perc_irf, perc_imt, perc_ivt
        IC 95% (Bas/Haut): qit_bas, qit_haut, icv_bas, icv_haut... (etc pour tous les indices).
        
        DATES (Format JJ/MM/AAAA) : date_naissance, date_passation
        
        TEXTE: {text_content[:9000]}
        Renvoie UNIQUEMENT un JSON valide.
        """
        response = model.generate_content(prompt)
        json_str = response.text.strip()
        if "```json" in json_str: json_str = json_str.split("```json")[1].split("```")[0]
        return json.loads(json_str)
    except Exception as e: st.error(f"Erreur extraction : {e}"); return None

def create_docx(text_content, prenom, age_str):
    doc = Document()
    doc.add_heading(f'Compte Rendu WISC-V : {prenom}', 0)
    doc.add_paragraph(f"Âge au bilan : {age_str}")
    p = doc.add_paragraph(); runner = p.add_run("AVERTISSEMENT : Document de travail. Analyse sous responsabilité du psychologue.")
    runner.bold = True; runner.italic = True
    doc.add_paragraph(text_content)
    bio = io.BytesIO(); doc.save(bio); return bio

# --- SIDEBAR ---
knowledge_base = ""
with st.sidebar:
    st.header("⚙️ Configuration")
    style_redac = st.radio("Destinataire / Style", 
                           ["Expert / MDPH (Technique & Clinique)", "Parents / École (Pédagogique)"], index=0)
    
    st.divider()
    st.header("📥 Import Q-GLOBAL")
    uploaded_qglobal = st.file_uploader("Rapport PDF", type=['pdf', 'txt'], key=f"uploader_{st.session_state.uploader_key}")
    
    if 'import_status' in st.session_state:
        status = st.session_state['import_status']
        if status['success']:
            st.success(status['msg'])
            if status['missing']: st.warning(f"⚠️ Manquant (mis à 0) :\n" + ", ".join(status['missing']))
        else: st.error(status['msg'])

    if uploaded_qglobal and st.button("🚀 Extraire Données"):
        with st.spinner("Analyse IA en cours..."):
            raw = read_file(uploaded_qglobal, uploaded_qglobal.name)
            data_ex = extract_qglobal_data(raw)
            missing = []; count = 0
            if data_ex:
                for k, v in data_ex.items():
                    if k == 'date_naissance' and v:
                        try: d=v.split('/'); st.session_state['jn']=int(d[0]); st.session_state['mn']=int(d[1]); st.session_state['an']=int(d[2]); count+=1
                        except: pass
                    elif k == 'date_passation' and v:
                        try: d=v.split('/'); st.session_state['jb']=int(d[0]); st.session_state['mb']=int(d[1]); st.session_state['ab']=int(d[2]); count+=1
                        except: pass
                    elif k in st.session_state:
                        try:
                            if v is None or v == "": val=0; missing.append(k)
                            else: val=float(v)
                            if val==0 and k not in missing: missing.append(k)
                            if 'perc' in k: st.session_state[k]=val
                            else: st.session_state[k]=int(val)
                            count+=1
                        except: st.session_state[k]=0; missing.append(k)
                st.session_state['import_status'] = {'success': True, 'msg': f"{count} champs importés.", 'missing': missing}
                st.rerun()
            else: st.session_state['import_status'] = {'success': False, 'msg': "Échec extraction IA.", 'missing': []}

    st.divider()
    st.header("📚 Bibliothèque")
    local_files = [f for f in os.listdir('.') if f.lower().endswith(('.pdf', '.txt')) and f not in ["requirements.txt", "app.py"]]
    if local_files:
        for f in local_files:
            if st.checkbox(f"📄 {f}", value=True, key=f):
                c = read_file(f, f)
                knowledge_base += f"\n--- SOURCE: {f} ---\n{c}\n"
        st.caption(f"Contexte : {len(knowledge_base)} chars")
        with st.expander("👀 Vérifier le contenu lu par l'IA"):
            st.text(knowledge_base[:3000] + "...") 
    else: st.warning("Pas de PDF trouvés.")
    
    st.divider()
    if st.button("🗑️ Nouvelle Analyse (Reset)", type="secondary"): reset_all()

# --- INTERFACE ---
st.header("1. Identité")
c1, c2, c3 = st.columns(3)
with c1: prenom = st.text_input("Prénom", placeholder="Ex: Lucas"); sexe = st.radio("Sexe", ["Garçon", "Fille"], horizontal=True); lateralite = st.radio("Latéralité", ["Droitier", "Gaucher"], horizontal=True)

with c2: 
    st.markdown("**Naissance**")
    cj, cm, ca = st.columns([1,1,1.5])
    with cj: jn = st.number_input("J", 1, 31, key="jn")
    with cm: mn = st.number_input("M", 1, 12, key="mn")
    with ca: an = st.number_input("A", 2000, 2030, key="an")
    try: dn = date(an, mn, jn)
    except: dn = date.today()
with c3:
    st.markdown("**Bilan**")
    cj, cm, ca = st.columns([1,1,1.5])
    with cj: jb = st.number_input("J", 1, 31, key="jb")
    with cm: mb = st.number_input("M", 1, 12, key="mb")
    with ca: ab = st.number_input("A", 2020, 2030, key="ab")
    try: dt = date(ab, mb, jb)
    except: dt = date.today()
    ans, mois = calculer_age(dn, dt)
    st.success(f"**{ans} ans {mois} mois**")

st.markdown("---")
st.header("2. Clinique")
c1, c2, c3 = st.columns(3)
obs = []
with c1: 
    st.markdown("**Attitude**")
    if st.checkbox("Anxiété"): obs.append("Anxiété perf.")
    if st.checkbox("Opposition"): obs.append("Opposition")
    if st.checkbox("Agitation"): obs.append("Agitation")
    if st.checkbox("Impulsivité"): obs.append("Impulsivité")
with c2:
    st.markdown("**Cognition**")
    if st.checkbox("Fatigabilité"): obs.append("Fatigabilité")
    if st.checkbox("Inattention"): obs.append("Inattention")
    if st.checkbox("Besoin relance"): obs.append("Besoin relance")
    if st.checkbox("Verbal +++"): obs.append("Logorrhée")
    if st.checkbox("Verbal ---"): obs.append("Mutisme/Pauvreté")
with c3:
    st.markdown("**Graphisme**")
    if st.checkbox("Crispation"): obs.append("Crispation")
    if st.checkbox("Lenteur graph."): obs.append("Lenteur graph.")
    st.markdown("---")
    st.markdown("🗣️ **Langue / Créole**")
    creole = st.radio("Usage", ["-- (Non/Peu)", "+- (Moyen)", "++ (Dominant)"], index=0, label_visibility="collapsed")

ana = st.text_area("Anamnèse", height=70, placeholder="Motif, histoire...")
obs_libre = st.text_area("Observations", height=70)

st.markdown("---")
st.header("3. Psychométrie")

st.subheader("A. Subtests (Notes Standard)")
c1, c2, c3, c4 = st.columns(4)
with c1: sim = st.number_input("SIM", 0, 19, key="sim")
with c2: voc = st.number_input("VOC", 0, 19, key="voc")
with c3: info = st.number_input("INF", 0, 19, key="info")
with c4: comp = st.number_input("COM", 0, 19, key="comp")
c1, c2 = st.columns(2)
with c1: cub = st.number_input("CUB", 0, 19, key="cub")
with c2: puz = st.number_input("PUZ", 0, 19, key="puz")
c1, c2, c3 = st.columns(3)
with c1: mat = st.number_input("MAT", 0, 19, key="mat")
with c2: bal = st.number_input("BAL", 0, 19, key="bal")
with c3: arit = st.number_input("ARI", 0, 19, key="arit")
c1, c2, c3 = st.columns(3)
with c1: memc = st.number_input("MCH", 0, 19, key="memc")
with c2: memi = st.number_input("MIM", 0, 19, key="memi")
with c3: seq = st.number_input("SLC", 0, 19, key="seq")
c1, c2, c3 = st.columns(3)
with c1: cod = st.number_input("COD", 0, 19, key="cod")
with c2: sym = st.number_input("SYM", 0, 19, key="sym")
with c3: bar = st.number_input("BAR", 0, 19, key="bar")

st.markdown("---")
st.subheader("B. Indices (Note / Perc. / IC)")

# Homogénéité
vicv, ticv = check_homogeneite_indice(sim, voc, "ICV")
vivs, tivs = check_homogeneite_indice(cub, puz, "IVS")
virf, tirf = check_homogeneite_indice(mat, bal, "IRF")
vimt, timt = check_homogeneite_indice(memc, memi, "IMT")
vivt, tivt = check_homogeneite_indice(sym, cod, "IVT")
etats = [ticv, tivs, tirf, timt, tivt]
nb_inv = sum([1 for x in [vicv, vivs, virf, vimt, vivt] if x is False])

# QIT
col_qit1, col_qit2, col_qit3, col_qit4, col_qit5 = st.columns(5)
with col_qit1: qit = st.number_input("QIT", 0, 160, key="qit")
with col_qit2: perc_qit = st.number_input("Perc", 0.0, 100.0, key="perc_qit")
with col_qit3: qit_bas = st.number_input("IC Bas", 0, 160, key="qit_bas")
with col_qit4: qit_haut = st.number_input("IC Haut", 0, 160, key="qit_haut")

# Indices
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown("**ICV**"); icv = st.number_input("S_ICV", 0, key="icv", label_visibility="collapsed")
    perc_icv = st.number_input("P_ICV", 0.0, key="perc_icv", label_visibility="collapsed")
    icv_bas = st.number_input("IB_ICV", 0, key="icv_bas", label_visibility="collapsed")
    icv_haut = st.number_input("IH_ICV", 0, key="icv_haut", label_visibility="collapsed")
    if ticv: st.caption(ticv)
with c2:
    st.markdown("**IVS**"); ivs = st.number_input("S_IVS", 0, key="ivs", label_visibility="collapsed")
    perc_ivs = st.number_input("P_IVS", 0.0, key="perc_ivs", label_visibility="collapsed")
    ivs_bas = st.number_input("IB_IVS", 0, key="ivs_bas", label_visibility="collapsed")
    ivs_haut = st.number_input("IH_IVS", 0, key="ivs_haut", label_visibility="collapsed")
    if tivs: st.caption(tivs)
with c3:
    st.markdown("**IRF**"); irf = st.number_input("S_IRF", 0, key="irf", label_visibility="collapsed")
    perc_irf = st.number_input("P_IRF", 0.0, key="perc_irf", label_visibility="collapsed")
    irf_bas = st.number_input("IB_IRF", 0, key="irf_bas", label_visibility="collapsed")
    irf_haut = st.number_input("IH_IRF", 0, key="irf_haut", label_visibility="collapsed")
    if tirf: st.caption(tirf)
with c4:
    st.markdown("**IMT**"); imt = st.number_input("S_IMT", 0, key="imt", label_visibility="collapsed")
    perc_imt = st.number_input("P_IMT", 0.0, key="perc_imt", label_visibility="collapsed")
    imt_bas = st.number_input("IB_IMT", 0, key="imt_bas", label_visibility="collapsed")
    imt_haut = st.number_input("IH_IMT", 0, key="imt_haut", label_visibility="collapsed")
    if timt: st.caption(timt)
with c5:
    st.markdown("**IVT**"); ivt = st.number_input("S_IVT", 0, key="ivt", label_visibility="collapsed")
    perc_ivt = st.number_input("P_IVT", 0.0, key="perc_ivt", label_visibility="collapsed")
    ivt_bas = st.number_input("IB_IVT", 0, key="ivt_bas", label_visibility="collapsed")
    ivt_haut = st.number_input("IH_IVT", 0, key="ivt_haut", label_visibility="collapsed")
    if tivt: st.caption(tivt)

with col_qit5:
    chk = [icv, ivs, irf, imt, ivt]
    if all(i > 0 for i in chk):
        disp = max(chk) - min(chk)
        if disp >= 23: st.error(f"⚠️ **Invalide** (Disp. {disp})"); h_txt = f"NON INTERPRÉTABLE (Disp. {disp})"
        elif nb_inv >= 2: st.warning("🟠 **Fragile**"); h_txt = f"FRAGILE ({nb_inv} ind. hétérogènes)"
        else: st.success("✅ **Homogène**"); h_txt = "Valide et Homogène"
    else: st.info("..."); h_txt = "N/A"

st.markdown("---")
# --- CALCUL SOMMES POUR AIDE (Avec Sécurité 0) ---
st.markdown("##### C. Indices Complémentaires")

def safe_sum(values):
    if all(v > 0 for v in values): return sum(values)
    return "Incomplet"

s_iag = safe_sum([sim, voc, cub, mat, bal])
s_icc = safe_sum([memc, memi, sym, cod])
s_inv = safe_sum([cub, puz, mat, bal, memi, cod])

st.caption(f"🧮 **Aide calcul (Somme Notes Standard) :** IAG = **{s_iag}** | ICC = **{s_icc}** | INV = **{s_inv}**")

c1, c2, c3 = st.columns(3)
with c1: st.markdown("**IAG**"); iag = st.number_input("IAG", 0, key="iag"); iag_bas = st.number_input("IB_IAG", 0, key="iag_bas", label_visibility="collapsed"); iag_haut = st.number_input("IH_IAG", 0, key="iag_haut", label_visibility="collapsed")
with c2: st.markdown("**ICC**"); icc = st.number_input("ICC", 0, key="icc"); icc_bas = st.number_input("IB_ICC", 0, key="icc_bas", label_visibility="collapsed"); icc_haut = st.number_input("IH_ICC", 0, key="icc_haut", label_visibility="collapsed")
with c3: st.markdown("**INV**"); inv = st.number_input("INV", 0, key="inv"); inv_bas = st.number_input("IB_INV", 0, key="inv_bas", label_visibility="collapsed"); inv_haut = st.number_input("IH_INV", 0, key="inv_haut", label_visibility="collapsed")

# --- ANALYSE ---
st.divider()
indices = {"ICV": icv, "IVS": ivs, "IRF": irf, "IMT": imt, "IVT": ivt}
valid_ind = {k: v for k, v in indices.items() if v > 0}

c1, c2 = st.columns([1, 1.5])
with c1:
    if len(valid_ind) >= 3: st.pyplot(plot_radar_chart(valid_ind))
with c2:
    if valid_ind:
        vals = list(valid_ind.values()); moy = np.mean(vals); et = np.std(vals)
        st.info(f"Moyenne Perso : **{moy:.1f}** | Écart-Type : **{et:.1f}**")
        intra_txt = f"Moyenne Perso: {moy:.1f}, ET: {et:.1f}."
        for k, v in valid_ind.items():
            d = v - moy
            if d >= 10: st.write(f"🟢 **{k}** : Force (+{d:.1f})"); intra_txt += f"- {k}: Force relative.\n"
            elif d <= -10: st.write(f"🔴 **{k}** : Faiblesse ({d:.1f})"); intra_txt += f"- {k}: Faiblesse relative.\n"
    else: intra_txt = ""

st.markdown("---")
if st.button("✨ GÉNÉRER L'ANALYSE EXPERT (MÉTHODE TERRIOT/OZENNE)", type="primary"):
    infos = f"{prenom}, {sexe}, {ans} ans. Date Bilan: {st.session_state.jb}/{st.session_state.mb}/{st.session_state.ab}. Latéralité: {lateralite}. Créole: {creole}."
    obs_txt = ", ".join(obs) + ". " + obs_libre
    
    # Construction Data (FILTRAGE RADICAL DES ZÉROS)
    if qit > 0:
        data = f"QIT: {qit} (Perc: {perc_qit}, IC: {qit_bas}-{qit_haut}). Validité: {h_txt}.\n"
    else:
        data = "QIT: Non calculé / Non administré.\n"

    # 2. Indices Principaux
    data += "Indices Administrés: "
    indices_data = []
    if icv > 0: indices_data.append(f"ICV {icv} (Perc {perc_icv}, IC {icv_bas}-{icv_haut})")
    if ivs > 0: indices_data.append(f"IVS {ivs} (Perc {perc_ivs}, IC {ivs_bas}-{ivs_haut})")
    if irf > 0: indices_data.append(f"IRF {irf} (Perc {perc_irf}, IC {irf_bas}-{irf_haut})")
    if imt > 0: indices_data.append(f"IMT {imt} (Perc {perc_imt}, IC {imt_bas}-{imt_haut})")
    if ivt > 0: indices_data.append(f"IVT {ivt} (Perc {perc_ivt}, IC {ivt_bas}-{ivt_haut})")
    data += ", ".join(indices_data) + ".\n"

    # 3. Indices Complémentaires
    data += "Indices Complémentaires: "
    compl_data = []
    if iag > 0: compl_data.append(f"IAG {iag} (IC {iag_bas}-{iag_haut})")
    if icc > 0: compl_data.append(f"ICC {icc} (IC {icc_bas}-{icc_haut})")
    if inv > 0: compl_data.append(f"INV {inv} (IC {inv_bas}-{inv_haut})")
    data += ", ".join(compl_data) + ".\n"

    # 4. Subtests (Le plus important : ne pas envoyer les 0)
    data += "Subtests (Notes Standard): "
    subs_map = {
        "Sim": sim, "Voc": voc, "Info": info, "Comp": comp,
        "Cub": cub, "Puz": puz, "Mat": mat, "Bal": bal,
        "Arit": arit, "MemC": memc, "MemI": memi, "Seq": seq,
        "Cod": cod, "Sym": sym, "Bar": bar
    }
    # On garde seulement ceux > 0
    valid_subs = [f"{k} {v}" for k, v in subs_map.items() if v > 0]
    data += ", ".join(valid_subs) + "."
    
    with st.spinner("Analyse approfondie (Clinique & Métrique)..."):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Rôle: Expert Psychologue WISC-V.
            
            DESTINATAIRE: {style_redac}.
            
            DONNÉES ENTRÉE:
            - Enfant: {infos}
            - Obs: {obs_txt}
            - Anamnèse: {ana}
            - Scores: {data}
            - Stats Intra: {intra_txt}
            
            <BIBLIOTHEQUE_REFERENCE>
            {knowledge_base}
            </BIBLIOTHEQUE_REFERENCE>
            
            CONSIGNE CRUCIALE DE HIERARCHIE :
            1. Pour la MÉTHODOLOGIE (calculs, validité, homogénéité), tu DOIS suivre scrupuleusement le contenu de <BIBLIOTHEQUE_REFERENCE> (notamment Grégoire, Ozenne).
            2. Pour le VOCABULAIRE DIAGNOSTIQUE en conclusion, utilise le DSM-5 / CIM-11.
            
            OBJECTIF QUALITATIF :
            Ne te contente pas de lister les scores. Tu dois EXPLIQUER et INTERPRÉTER.
            - Utilise des connecteurs logiques : "ce qui suggère que...", "probablement en raison de...", "ce résultat contraste avec...".
            - Formule des HYPOTHÈSES sur les mécanismes cognitifs sous-jacents (ex: déficit d'encodage vs déficit de récupération).
            - Analyse les ÉCARTS : Si l'ICV est > IVS, qu'est-ce que ça implique concrètement ?
            
            STRUCTURE DU COMPTE RENDU :
            
            1. VALIDITÉ DES INDICES GLOBAUX (Suivre méthode Bibliothèque)
               - Vérifier homogénéité QIT. Si invalide, passer à IAG/ICC/INV selon les critères de la bibliothèque.
            
            2. ANALYSE INTER-INDIVIDUELLE (NORMATIVE) -> FOCUS INDICES UNIQUEMENT
               - Parles des INDICES (QIT, ICV, etc.) par rapport à la norme (100).
               - INTERDICTION de parler des subtests ici.
               - Analyse la dispersion des indices (profil harmonique ou disharmonique ?).
            
            3. ANALYSE INTRA-INDIVIDUELLE (IPSATIVE) -> FOCUS SUBTESTS
               - Analyses les SUBTESTS (Cubes, Similitudes...) par rapport à la moyenne de l'enfant ({moy if valid_ind else 'N/A'}).
               - Utilise les seuils de la bibliothèque (<4 Très faible, etc.).
               - Lier chaque résultat à une hypothèse cognitive/clinique. Pourquoi a-t-il réussi/échoué ? (Planification ? Attention ? Vitesse ?).
            
            4. SYNTHÈSE DIAGNOSTIQUE & RECOMMANDATIONS
               - Croiser avec l'anamnèse.
               - Hypothèses (TDAH, TSA, etc.).
               - Conseils pratiques.
            
            Rédige le bilan final avec un ton professionnel, argumenté et clinique.
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            f = create_docx(res.text, prenom, f"{ans}a{mois}m")
            st.download_button("📄 Télécharger Word", f, f"Bilan_{prenom}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
        except Exception as e: st.error(f"Erreur : {e}")
