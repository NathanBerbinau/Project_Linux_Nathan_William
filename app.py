import streamlit as st
from streamlit_autorefresh import st_autorefresh
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
    st.session_state['last_update'] = None

st_autorefresh(interval=1000, key="ui_clock")

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

    if auto_refresh:
        refresh_count=st_autorefresh(interval=300_000, key="global_refresh")
    else:
        refresh_count=0

    if st.session_state['last_update'] is not None:
        elapsed = int(time.time() - st.session_state['last_update'])
        st.sidebar.info(
            f"Last update: {elapsed // 60} min {elapsed % 60:02d} s ago"
        )
    else:
        st.sidebar.info("Last update: N/A")



    if page_selection == "Single Asset Analysis (Quant A)":
        st.sidebar.subheader("Module Quant A")
        render_quant_a_dashboard(refresh_count)
    else:
        st.sidebar.subheader("Module Quant B")
        render_quant_b_dashboard(refresh_count)
    #Footer
    st.sidebar.markdown("---")


if __name__ == "__main__":
    main()
