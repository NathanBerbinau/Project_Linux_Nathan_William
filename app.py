import streamlit as st
import time

from modules.Quant_A.dashboard import render_quant_a_dashboard
from modules.Quant_B.qwant_b import render_quant_b_dashboard

# Page configuration
st.set_page_config(
    page_title="Quant Finance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.markdown(
        '<h1 style="text-align: center; color: #1f77b4;">Quantitative Finance Dashboard</h1>',
        unsafe_allow_html=True
    )
    st.markdown("**Real-time market analysis with backtesting capabilities**")
    st.markdown("---")

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (every 5 min)", value=False)

    st.sidebar.title("Navigation")
    st.sidebar.info("""
    **About this Dashboard:**
    - Real-time market data
    - Multiple backtesting strategies
    - Performance analytics
    - Daily automated reports

    Built for asset management professionals
    """)

    # Render dashboards
    if auto_refresh:
        placeholder = st.empty()
        while True:
            with placeholder.container():
                st.header("Quant A Dashboard")
                render_quant_a_dashboard()
                
                st.header("Quant B Dashboard")
                render_quant_b_dashboard()
            time.sleep(300)  # 5 minutes
    else:
        st.header("Quant A Dashboard")
        render_quant_a_dashboard()
        
        st.header("Quant B Dashboard")
        render_quant_b_dashboard()

    # Footer
    st.sidebar.markdown("---")

if __name__ == "__main__":
    main()
