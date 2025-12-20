import streamlit as st
import time
from modules.Quant_A.dashboard import render_quant_a_dashboard
from modules.Quant_B.dashboard import render_quant_b_dashboard

# Page configuration
st.set_page_config(
    page_title="Quant Finance Dashboard",
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

    st.sidebar.title("Navigation")
    page_selection = st.sidebar.radio(
        "Select Module",
        ["Single Asset Analysis (Quant A)", "Portfolio Analysis (Quant B)"]
    )
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (every 5 min)", value=False)

    st.sidebar.info("""
        **About this Dashboard:**
        - Real-time market data
        - Multiple backtesting strategies
        - Performance analytics
        - Daily automated reports
        """)

    if page_selection == "Single Asset Analysis (Quant A)":
        if auto_refresh:
            placeholder = st.empty()
            while True:
                with placeholder.container():
                    render_quant_a_dashboard()
                    st.sidebar.subheader("Module Quant A")
                time.sleep(300)  # 5 minutes
        else:
            render_quant_a_dashboard()
            st.sidebar.subheader("Module Quant A")

    else:
        if auto_refresh:
            placeholder = st.empty()
            while True:
                with placeholder.container():
                    render_quant_b_dashboard()
                    st.sidebar.subheader("Module Quant B")
                    st.sidebar.info(f"Last Refresh: {st.session_state['last_update']}")
                time.sleep(300)  # 5 minutes
        else:
            render_quant_b_dashboard()
            st.sidebar.subheader("Module Quant B")
            st.sidebar.info(f"Last Refresh: {st.session_state['last_update']}")
    #Footer
    st.sidebar.markdown("---")


if __name__ == "__main__":
    main()
