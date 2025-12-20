import streamlit as st
import time
from modules.Quant_A.dashboard import render_quant_a_dashboard
from modules.Quant_B.dashboard import render_quant_b_dashboard

# Page configuration
st.set_page_config(
    page_title="Quant Finance Dashboard",
    #page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation de l'état pour l'heure de mise à jour si elle n'existe pas
if 'last_update' not in st.session_state:
    st.session_state['last_update'] = 'N/A'

def main():
    st.markdown('<h1 style="text-align: center; color: #1f77b4;"> Quantitative Finance Dashboard</h1>',
                unsafe_allow_html=True)
    st.markdown("**Real-time market analysis with backtesting capabilities**")
    st.markdown("---")

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (every 5 min)", value=False)

    st.sidebar.title("Navigation")
    
    # -----------------------------------------------------
    # NOUVELLE LOGIQUE : SÉLECTEUR DE MODULE DANS LA SIDEBAR
    
    page_selection = st.sidebar.radio( # <-- AJOUT DU SÉLECTEUR DE PAGE
        "Choisissez le Module", 
        ["Analyse Actif Unique (Quant A)", "Analyse de Portefeuille (Quant B)"]
    )
    
    # DÉTERMINER LA FONCTION DE RENDU
    if page_selection == "Analyse Actif Unique (Quant A)":
        render_function = render_quant_a_dashboard
        st.sidebar.subheader("Module Quant A")
        
    else: # Analyse de Portefeuille (Quant B)
        render_function = render_quant_b_dashboard
        st.sidebar.subheader("Module Quant B")
        # Afficher l'heure de la dernière mise à jour des données (Exigence 5)
        st.sidebar.info(f"Dernière Actualisation: {st.session_state['last_update']}")


    # FIN DE LA NOUVELLE LOGIQUE
    # -----------------------------------------------------

    st.sidebar.info("""
    **About this Dashboard:**
    - Real-time market data
    - Multiple backtesting strategies
    - Performance analytics
    - Daily automated reports

    Built for asset management professionals
    """)

    # Render dashboard (MODIFIÉ POUR UTILISER render_function)
    if auto_refresh:
        placeholder = st.empty()
        while True:
            with placeholder.container():
                render_function() # <-- Appel dynamique
            time.sleep(300) # 5 minutes
    else:
        render_function() # <-- Appel dynamique

    # Footer
        st.sidebar.markdown("---")


if __name__ == "__main__":
    main()
