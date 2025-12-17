import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="WISC-V Analyst (Méthode Grégoire)", page_icon="🧠", layout="wide")

st.title("🧠 Analyseur WISC-V - Aide à la rédaction CDO")
st.markdown("""
*Basé sur la méthodologie clinique de Jacques Grégoire.*
Cet outil aide à l'interprétation psychométrique (Inter & Intra). **Il ne remplace pas le jugement clinique.**
""")

# --- FONCTIONS UTILITAIRES ---

def get_qualitative_description(score):
    if score >= 130: return "Très Supérieur"
    if 120 <= score < 130: return "Supérieur"
    if 110 <= score < 120: return "Moyen Fort"
    if 90 <= score < 110: return "Moyen"
    if 80 <= score < 90: return "Moyen Faible"
    if 70 <= score < 80: return "Fragile (Zone limite)"
    if score < 70: return "Très Faible"
    return ""

def check_homogeneity(indices):
    # Méthode Grégoire : QIT interprétable si étendue < 23 (seuil strict) ou < 40 (seuil clinique souple selon contexte)
    # Ici on prend une approche nuancée
    valid_scores = [v for k, v in indices.items() if v > 0]
    if not valid_scores:
        return "N/A", 0
    
    ecart_max = max(valid_scores) - min(valid_scores)
    
    if ecart_max < 23:
        status = "Homogène (QIT valide)"
    elif ecart_max < 40:
        status = "Hétérogène (QIT à nuancer, voir IAG/ICC)"
    else:
        status = "Très Hétérogène (QIT non valide, privilégier l'analyse par indices)"
    
    return status, ecart_max

# --- SIDEBAR : SAISIE DES DONNÉES ---
with st.sidebar:
    st.header("1. Données Administratives")
    sexe = st.radio("Sexe", ["Garçon", "Fille"])
    ddn = st.date_input("Date de naissance", min_value=date(2000, 1, 1))
    date_bilan = st.date_input("Date du bilan", min_value=date(2023, 1, 1))
    
    # Calcul Age
    age_years = date_bilan.year - ddn.year - ((date_bilan.month, date_bilan.day) < (ddn.month, ddn.day))
    st.info(f"Âge au moment du bilan : {age_years} ans")

    st.header("2. Notes Standards (Subtests)")
    st.caption("Laisser à 0 ou vide si non passés")
    
    col1, col2 = st.columns(2)
    with col1:
        cubes = st.number_input("Cubes (IVS)", 0, 19, 0)
        similitudes = st.number_input("Similitudes (ICV)", 0, 19, 0)
        matrices = st.number_input("Matrices (IRF)", 0, 19, 0)
        mem_chiffres = st.number_input("Mém. Chiffres (IMT)", 0, 19, 0)
        code = st.number_input("Code (IVT)", 0, 19, 0)
        vocabulaire = st.number_input("Vocabulaire (ICV)", 0, 19, 0)
        balances = st.number_input("Balances (IRF)", 0, 19, 0)
        puzzles = st.number_input("Puzzles Visuels (IVS)", 0, 19, 0)
    with col2:
        mem_images = st.number_input("Mém. Images (IMT)", 0, 19, 0)
        symboles = st.number_input("Symboles (IVT)", 0, 19, 0)
        info = st.number_input("Information (Sec)", 0, 19, 0)
        seq_lc = st.number_input("Séquence L-C (Sec)", 0, 19, 0)
        barrage = st.number_input("Barrage (Sec)", 0, 19, 0)
        comprehension = st.number_input("Compréhension (Sec)", 0, 19, 0)
        arithmetique = st.number_input("Arithmétique (Sec)", 0, 19, 0)

    st.header("3. Notes Composites (Indices)")
    st.caption("Intervalle de confiance 95%")
    icv = st.number_input("ICV (Verbal)", 40, 160, 0)
    ivs = st.number_input("IVS (Visuospatial)", 40, 160, 0)
    irf = st.number_input("IRF (Fluide)", 40, 160, 0)
    imt = st.number_input("IMT (Mém. Travail)", 40, 160, 0)
    ivt = st.number_input("IVT (Vitesse)", 40, 160, 0)
    qit = st.number_input("QIT (Total)", 40, 160, 0)
    
    st.markdown("---")
    st.subheader("Indices Optionnels")
    iag = st.number_input("IAG (Aptitude Gle)", 40, 160, 0)
    icc = st.number_input("ICC (Comp. Cognitive)", 40, 160, 0)
    inv = st.number_input("INV (Non Verbal)", 40, 160, 0)

# --- TRAITEMENT ET ANALYSE ---

# 1. Dictionnaire des données
indices_dict = {"ICV": icv, "IVS": ivs, "IRF": irf, "IMT": imt, "IVT": ivt}
# Filtrer les indices non saisis
indices_actifs = {k: v for k, v in indices_dict.items() if v > 0}

subtests_principaux = [cubes, similitudes, matrices, mem_chiffres, code, vocabulaire, balances, puzzles, mem_images, symboles]
subtests_principaux = [s for s in subtests_principaux if s > 0]

# --- GÉNÉRATION DU RAPPORT ---

if st.button("Générer l'Analyse Clinique"):
    
    if not indices_actifs:
        st.error("Veuillez saisir au moins les indices principaux.")
    else:
        # A. ANALYSE INTER-INDIVIDUELLE (Validité QIT et Niveau)
        homogeneite, ecart_max = check_homogeneity(indices_actifs)
        
        # B. ANALYSE INTRA-INDIVIDUELLE (Points forts/faibles relatifs)
        # Calcul de la moyenne des notes standards (MSS) de l'enfant
        if len(subtests_principaux) > 0:
            moyenne_personnelle = sum(subtests_principaux) / len(subtests_principaux)
        else:
            moyenne_personnelle = 10 # Valeur par défaut théorique
            
        # Seuils de significativité (Approximation Grégoire : +/- 3 points par rapport à la moyenne)
        seuil_critique = 3.0
        
        points_forts = []
        points_faibles = []
        
        # Mapping Subtest -> Nom et Score
        map_subtests = {
            "Similitudes": similitudes, "Vocabulaire": vocabulaire, "Information": info, "Compréhension": comprehension,
            "Cubes": cubes, "Puzzles Visuels": puzzles,
            "Matrices": matrices, "Balances": balances, "Arithmétique": arithmetique,
            "Mém. Chiffres": mem_chiffres, "Mém. Images": mem_images, "Séquence L-C": seq_lc,
            "Code": code, "Symboles": symboles, "Barrage": barrage
        }
        
        for nom, note in map_subtests.items():
            if note > 0:
                diff = note - moyenne_personnelle
                if diff >= seuil_critique:
                    points_forts.append(f"{nom} ({note})")
                elif diff <= -seuil_critique:
                    points_faibles.append(f"{nom} ({note})")

        # --- AFFICHAGE SELON LA TRAME CDO ---
        
        st.markdown("## III. EVALUATION PSYCHOMETRIQUE")
        st.info("Copier-coller le texte ci-dessous dans la section III du document .odt")
        
        texte_analyse = f"""
**Validité globale du protocole :**
L'analyse de la dispersion des indices montre un profil {homogeneite.lower()} (Écart maximal de {ecart_max} points).
"""
        if ecart_max >= 23:
            texte_analyse += "Le QIT ne peut donc pas résumer à lui seul l'efficience intellectuelle de l'enfant. Il est nécessaire d'analyser les indices séparément et de s'appuyer potentiellement sur l'IAG (Indice d'Aptitude Générale) pour estimer le potentiel de raisonnement pur, libéré des contraintes de vitesse et de mémoire de travail.\n"
        else:
            texte_analyse += f"Le QIT est donc une mesure valide de l'efficience globale. Il se situe à {qit} (Intervalle de confiance 95% : [{qit-6}-{qit+6}]), ce qui correspond à un niveau {get_qualitative_description(qit)}.\n"

        texte_analyse += "\n**Analyse par domaines (Inter-individuelle) :**\n"
        for nom, val in indices_actifs.items():
            texte_analyse += f"- **{nom} ({val})** : Niveau {get_qualitative_description(val)}. "
            if nom == "ICV": texte_analyse += "Reflète l'intelligence cristallisée, la compréhension verbale et l'accès à la culture. "
            if nom == "IVS": texte_analyse += "Mesure le raisonnement visuo-spatial et l'intégration des relations spatiales. "
            if nom == "IRF": texte_analyse += "Évalue l'intelligence fluide, la capacité à résoudre des problèmes nouveaux sans support langagier. "
            if nom == "IMT": texte_analyse += "Indique l'efficacité de la mémoire de travail (maintien et manipulation mentale d'informations). "
            if nom == "IVT": texte_analyse += "Traduit la vitesse de traitement graphomotrice et l'efficacité attentionnelle. "
            texte_analyse += "\n"

        texte_analyse += "\n**Analyse Clinique Intra-individuelle (Forces et Fragilités) :**\n"
        texte_analyse += f"Par rapport à sa propre moyenne de fonctionnement (Moyenne des notes standards = {round(moyenne_personnelle, 1)}), on observe :\n"
        
        if points_forts:
            texte_analyse += f"- **Des points forts relatifs** (Ressources mobilisables) en : {', '.join(points_forts)}. Cela suggère une aisance particulière pour...\n"
        else:
            texte_analyse += "- Aucun point fort significatif ne se détache par rapport à son fonctionnement global (profil plat).\n"
            
        if points_faibles:
            texte_analyse += f"- **Des fragilités relatives** en : {', '.join(points_faibles)}. Ces chutes de performance peuvent s'expliquer par...\n"
        else:
            texte_analyse += "- Aucune chute significative n'est observée (profil homogène).\n"
            
        # Analyse spécifique IAG vs ICC (Grégoire)
        if iag > 0 and icc > 0:
            diff_iag_icc = iag - icc
            texte_analyse += "\n**Comparaison Haut Potentiel / Efficience Cognitive :**\n"
            if abs(diff_iag_icc) >= 10:
                sens = "supérieur" if diff_iag_icc > 0 else "inférieur"
                texte_analyse += f"On note une dissociation importante. L'IAG (Raisonnement) est nettement {sens} à l'ICC (Outils cognitifs : Mémoire/Vitesse). "
                if diff_iag_icc > 0:
                    texte_analyse += "Cela est classique chez les profils où l'instrumental (attention, graphisme) freine l'expression du potentiel intellectuel (ex: TDAH, Dyspraxie, Anxiété de performance).\n"
                else:
                    texte_analyse += "Les compétences instrumentales sont très efficientes et soutiennent le raisonnement.\n"
        
        if inv > 0:
             texte_analyse += f"\n**Indice Non Verbal (INV) : {inv}**. Utile dans ce contexte pour évaluer l'intelligence en minimisant la charge linguistique (ex: allophone ou troubles du langage).\n"

        st.text_area("Texte généré pour Section III", value=texte_analyse, height=400)
        
        # --- SECTION CONCLUSION ---
        st.markdown("## IV. CONCLUSION DU BILAN")
        st.warning("Suggestions de formulations pour compléter la section IV.")
        
        conclu_scolaire = ""
        if qit < 70 and ecart_max < 23:
            conclu_scolaire = "Les résultats objectivent des difficultés cognitives globales et homogènes, situant l'efficience dans la zone du retard intellectuel léger."
        elif qit < 80:
            conclu_scolaire = "Les résultats témoignent d'un fonctionnement cognitif fragile, en zone limite, qui peut fragiliser les apprentissages scolaires classiques."
        elif ecart_max >= 23:
            conclu_scolaire = "Le profil est complexe et dysharmonique. Les potentialités de raisonnement (voir IAG) sont supérieures à l'efficience globale constatée, suggérant que des troubles instrumentaux (attentionnels/instrumentaux) ou émotionnels impactent la scolarité."
        else:
            conclu_scolaire = "L'efficience intellectuelle est dans la moyenne, suggérant que les difficultés scolaires ne sont pas d'origine purement cognitive."

        conclu_psycho = "L'analyse qualitative suggère..."
        if ivt < 85 or imt < 85:
            conclu_psycho += " une fatigabilité cognitive importante et un coût attentionnel élevé."
        if icv > irf + 15:
            conclu_psycho += " un fort investissement de la sphère verbale pouvant masquer des fragilités en raisonnement fluide."
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("### Sur le plan scolaire (Proposition)")
            st.write(conclu_scolaire)
            if iag >= 90 and (imt < 85 or ivt < 85):
                st.markdown("👉 *À noter :* L'élève possède les ressources de raisonnement nécessaires pour le programme, mais ses outils cognitifs (mémoire/vitesse) sont saturés, nécessitant des adaptations.")
        
        with col_c2:
            st.markdown("### Sur le plan psychométrique (Synthèse)")
            st.write(f"Fonctionnement global {homogeneite.lower()}.")
            st.write(conclu_psycho)
            if points_forts:
                st.markdown(f"**Appuis** : {', '.join([p.split('(')[0] for p in points_forts])}")

        st.markdown("### Suggestion Préconisations (Section V)")
        if ivt < 85:
            st.write("- Tiers temps ou allègement de la charge graphique (passer par l'oral).")
            st.write("- Supports aérés pour compenser la lenteur de traitement visuel.")
        if imt < 85:
            st.write("- Consignes courtes, fractionnées.")
            st.write("- Support visuel pour étayer la mémoire auditive défaillante.")
        if icv < 80:
            st.write("- Vérification systématique de la compréhension des consignes verbales.")
            st.write("- Orthophonie si non mis en place.")
