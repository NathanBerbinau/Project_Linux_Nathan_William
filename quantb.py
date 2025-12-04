class my_class(object):
    ######quant b part

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# --- Fonction de Récupération de Données (Exigence 1, 15, 17) ---
# Utilisation de st.cache_data avec ttl=300 (5 minutes) pour l'actualisation (Exigence 5, 21)
@st.cache_data(ttl=300)
def fetch_portfolio_data(assets_list, start_date):
    """Récupère les données historiques ajustées pour une liste d'actifs."""
    try:
        data = yf.download(assets_list, start=start_date)['Adj Close']
        # Assurer que 'data' est un DataFrame même si un seul actif est demandé
        if isinstance(data, pd.Series):
            data = data.to_frame(name=assets_list[0])
        
        # Mettre à jour l'heure de la dernière actualisation pour l'affichage dans le dashboard
        st.session_state['last_update'] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        return data.dropna()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données de Yahoo Finance : {e}")
        return pd.DataFrame()

# --- Fonction de Calcul des Métriques (Exigence 42) ---
def calculate_portfolio_metrics(portfolio_value, rf_rate=0.04):
    """Calcule le Rendement Annuel, Volatilité, et Sharpe Ratio."""
    
    returns = portfolio_value.pct_change().dropna()
    if returns.empty:
        return 0, 0, 0

    annual_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0])**(252/len(portfolio_value)) - 1
    annual_volatility = returns.std() * np.sqrt(252)
    
    # Sharpe Ratio (hypothèse de 252 jours de trading)
    sharpe_ratio = (annual_return - rf_rate) / annual_volatility if annual_volatility != 0 else 0

    return annual_return, annual_volatility, sharpe_ratio

# --- Fonction de Rendu du Module B ---
def render_page():
    st.subheader("🛠️ Paramètres du Portefeuille (Multi-Asset)")

    # 1. Contrôles Utilisateur (Exigence 41, 43)
    default_assets = ['AAPL', 'MSFT', 'GOOGL']
    assets_options = st.multiselect(
        "Sélectionner les Actifs (min. 3)",
        ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'EURUSD=X'],
        default=default_assets
    )

    if len(assets_options) < 3:
        st.warning("Veuillez sélectionner au moins **3 actifs** pour l'analyse de portefeuille.")
        return

    col_date, col_rebal = st.columns([1, 1])
    with col_date:
        start_date = st.date_input("Date de Début", pd.to_datetime('2024-01-01'))
    with col_rebal:
        st.selectbox("Fréquence de Rééquilibrage", ['Mensuel', 'Trimestriel', 'Annuel', 'Jamais'], index=0)

    # 2. Récupération des Données
    data = fetch_portfolio_data(assets_options, start_date)
    if data.empty:
        return

    st.markdown("---")
    
    # 3. Calcul de la Stratégie (Pondérations) (Exigence 42, 43)
    st.subheader("Pondération des Actifs")
    weights_type = st.radio("Sélectionner le type de Pondération", ["Pondération Égale", "Pondération Personnalisée"], horizontal=True)

    if weights_type == "Pondération Égale":
        weights = np.array([1/len(assets_options)] * len(assets_options))
    else:
        # Interface pour Pondération Personnalisée
        st.info("Attribuez des poids dont la somme est égale à 100%")
        input_weights = []
        for asset in assets_options:
            input_weights.append(st.number_input(f"Poids pour {asset} (%)", min_value=0, max_value=100, value=int(100/len(assets_options))))
        
        sum_weights = sum(input_weights)
        if sum_weights != 100:
            st.warning(f"La somme des poids est de {sum_weights}%. Elle doit être de 100%.")
            return
        weights = np.array(input_weights) / 100.0

    # Calcul du rendement cumulé du portefeuille
    normalized_prices = data / data.iloc[0]
    portfolio_value = (normalized_prices * weights).sum(axis=1) * 100 # Base 100 pour la comparaison

    # 4. Affichage des Résultats

    st.subheader("📈 Comparaison des Performances (Exigence 44)")
    
    # Graphique Principal : Actifs Individuels (normalisés) VS Portefeuille (Exigence 44)
    plot_data = normalized_prices.copy() * 100 # Normaliser la base à 100
    plot_data['Portefeuille'] = portfolio_value
    
    st.line_chart(plot_data, use_container_width=True)
    st.caption("Valeur Cumulative des Actifs (Base 100) et du Portefeuille")

    st.markdown("---")

    # 5. Métriques du Portefeuille (Exigence 42)
    st.subheader("📊 Métriques Clés du Portefeuille")
    
    annual_return, annual_volatility, sharpe_ratio = calculate_portfolio_metrics(portfolio_value)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Rendement Annualisé", f"{annual_return:.2%}")
    col2.metric("Volatilité Annualisée", f"{annual_volatility:.2%}")
    col3.metric("Sharpe Ratio (RF=4%)", f"{sharpe_ratio:.2f}") 

    st.subheader("🕸️ Matrice de Corrélation (Exigence 42)")
    correlation_matrix = data.pct_change().corr()
    
    # Affichage de la matrice de corrélation
    st.dataframe(correlation_matrix.style.background_gradient(cmap='coolwarm'), use_container_width=True)
    st.caption("Aide à visualiser les effets de diversification[cite: 42].")
    pass




