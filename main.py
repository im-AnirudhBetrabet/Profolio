import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
from kiteconnect import KiteConnect
from contextlib import contextmanager
from styles import apply_custom_css
from data_manager import load_cached_portfolio, save_portfolio, process_live_data

# 1. Page Config & CSS

@contextmanager
def premium_spinner(text="Processing..."):
    """A custom context manager to replace st.spinner with a glassmorphic UI."""
    placeholder = st.empty()
    placeholder.markdown(f"""
        <div class="custom-loader-container">
            <div class="custom-loader"></div>
            <div class="custom-loader-text">{text}</div>
        </div>
    """, unsafe_allow_html=True)
    try:
        yield
    finally:
        placeholder.empty()

st.set_page_config(page_title="ProFolio", layout="wide", initial_sidebar_state="expanded")
apply_custom_css()

st.title("💠 ProFolio Command Center")


# 3. Sidebar Authentication & Controls
import os
import json

CRED_FILE = "credentials.json"


# Helper function to load credentials
def load_creds():
    """Loads all saved broker credentials from the JSON file."""
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f:
                c = json.load(f)
                # Backward-compatibility: If it's the old single-broker format, wrap it
                if "broker" in c:
                    broker_name = c.pop("broker")
                    return {broker_name: c}

                # If it's the very first legacy format (no broker key)
                if "api_key" in c and "broker" not in c and "Zerodha" not in c:
                    return {"Zerodha": c}

                return c
        except json.JSONDecodeError:
            return {}
    return {}


with st.sidebar:
    st.header("⚙️ Settings & Sync")

    # --- 1. Broker Selection ---
    selected_broker = st.radio("Select Broker API:", ["Zerodha", "Groww"], horizontal=True)
    st.divider()

    # Load the master dictionary of all credentials
    all_creds = load_creds()

    # Extract credentials just for the currently selected broker
    active_creds = all_creds.get(selected_broker)

    raw_stocks = load_cached_portfolio(selected_broker)

    if raw_stocks is None:
        st.warning(f"Not Connected to {selected_broker}")

        # Step 1: No credentials exist for the selected broker
        if active_creds is None:
            st.write(f"Step 1: Save your {selected_broker} credentials.")

            if selected_broker == "Zerodha":
                api_key_input = st.text_input("API Key", type="password", key="z_key")
                api_secret_input = st.text_input("API Secret", type="password", key="z_sec")

                if st.button("Save Credentials", width='stretch'):
                    all_creds["Zerodha"] = {"api_key": api_key_input, "api_secret": api_secret_input}
                    with open(CRED_FILE, "w") as f:
                        json.dump(all_creds, f)
                    st.success("Saved! Refreshing...")
                    st.rerun()

            elif selected_broker == "Groww":
                groww_api_key = st.text_input("Groww API Key", type="password", key="g_key")
                groww_api_secret = st.text_input("Groww API Secret", type="password", key="g_sec")

                if st.button("Save Credentials", width='stretch'):
                    all_creds["Groww"] = {"api_key": groww_api_key, "api_secret": groww_api_secret}
                    with open(CRED_FILE, "w") as f:
                        json.dump(all_creds, f)
                    st.success("Saved! Refreshing...")
                    st.rerun()
        # 3. If credentials exist, proceed with the seamless login flow
        else:
            # --- ZERODHA FLOW ---
            if selected_broker == "Zerodha":
                api_key = active_creds["api_key"]
                api_secret = active_creds["api_secret"]
                kite = KiteConnect(api_key=api_key)
                login_url = kite.login_url()

                st.write("Step 2: Authenticate with Zerodha.")
                st.markdown(f"**[👉 Click Here to Log In]({login_url})**")

                query_params = st.query_params

                if "request_token" in query_params:
                    request_token = query_params["request_token"]
                    with premium_spinner("Authenticating with Zerodha..."):
                        try:
                            data = kite.generate_session(request_token, api_secret=api_secret)
                            kite.set_access_token(data["access_token"])
                            real_holdings = kite.holdings()

                            formatted_data = []
                            for item in real_holdings:
                                formatted_data.append({
                                    "ticker": item['tradingsymbol'],
                                    "qty": item['quantity'],
                                    "avg_price": item['average_price']
                                })

                            # Optional: You could save broker info in the cache if needed later
                            save_portfolio(selected_broker, formatted_data)
                            st.query_params.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Sync Failed: {e}")

            # --- GROWW FLOW ---
            elif selected_broker == "Groww":
                st.write("Step 2: Sync Groww Data.")

                if st.button("Sync Live Holdings", type="primary", width='stretch'):
                    with premium_spinner("Fetching from Groww Cloud..."):
                        try:
                            from growwapi import GrowwAPI
                            import pyotp

                            access_token = GrowwAPI.get_access_token(api_key=active_creds["api_key"], secret=active_creds["api_secret"])
                            # Using the specific Groww keys from active_creds
                            groww = GrowwAPI(access_token)

                            real_holdings = groww.get_holdings_for_user()
                            print(real_holdings)
                            formatted_data = []
                            for item in real_holdings.get("holdings"):
                                formatted_data.append({
                                    "ticker": item['trading_symbol'],
                                    "qty": item['quantity'],
                                    "avg_price": item['average_price']
                                })
                            save_portfolio(selected_broker, formatted_data)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Sync Failed. Check token. Details: {e}")

            # Option to reset credentials ONLY for the active broker
            if st.button(f"Reset {selected_broker} Credentials", type="secondary", width='stretch'):
                all_creds.pop(selected_broker, None)
                with open(CRED_FILE, "w") as f:
                    json.dump(all_creds, f)
                st.rerun()

    else:
        st.success("🟢 Connected to Cache")
        if st.button("🔄 Refresh Live Market Prices", width='stretch'):
            st.cache_data.clear()
            st.rerun()

        if st.button(f"⚠️ Disconnect {selected_broker}", type="primary", width='stretch'):

            # 1. Selectively delete from the portfolio cache
            if os.path.exists("saved_portfolio.json"):
                try:
                    with open("saved_portfolio.json", "r") as f:
                        port_data = json.load(f)
                    if isinstance(port_data, dict):
                        port_data.pop(selected_broker, None)
                        with open("saved_portfolio.json", "w") as f:
                            json.dump(port_data, f)
                except json.JSONDecodeError:
                    pass

            # 2. Selectively delete from the credentials cache
            if os.path.exists(CRED_FILE):
                try:
                    with open(CRED_FILE, "r") as f:
                        cred_data = json.load(f)
                    if isinstance(cred_data, dict):
                        cred_data.pop(selected_broker, None)
                        with open(CRED_FILE, "w") as f:
                            json.dump(cred_data, f)
                except json.JSONDecodeError:
                    pass

            # Clear Streamlit's in-memory cache and reload
            st.cache_data.clear()
            st.rerun()

# 4. Main App Routing
if raw_stocks is None:
    st.info("👈 Please sync your broker account in the sidebar to view your dashboard.")
elif len(raw_stocks) == 0:
    # --- THE PREMIUM EMPTY STATE ---
    st.markdown("""
    <div style="text-align: center; padding: 5rem 2rem; background: rgba(255,255,255,0.02); backdrop-filter: blur(10px); border-radius: 1rem; border: 1px solid rgba(255,255,255,0.05); margin-top: 2rem;">
        <h2 style="color: #E2E8F0; margin-bottom: 1rem;">🌱 Your Portfolio is a Blank Canvas</h2>
        <p style="color: #9CA3AF; font-size: 1.1rem; margin-bottom: 0.5rem;">It looks like you don't have any active holdings in your linked broker account yet.</p>
        <p style="color: #9CA3AF; font-size: 1.1rem;">Once you make your first investment, hit the <b>Sync</b> button in the sidebar to watch your dashboard come to life.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Process the data
    with premium_spinner("Fetching live market data..."):
        df = process_live_data(raw_stocks)

    # Calculate high-level metrics
    total_invested = df["Invested"].sum()
    total_current = df["Current Value"].sum()
    total_return_pct = ((total_current - total_invested) / total_invested) * 100
    abs_return = total_current - total_invested

    # --- TOP GLANCE METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Invested", f"₹{total_invested:,.0f}", height='stretch')
    col2.metric("Current Value", f"₹{total_current:,.0f}", f"{total_return_pct:.2f}% Total", height='stretch')
    col3.metric("Absolute Return", f"₹{abs_return:,.0f}", height='stretch')

    st.divider()

    # --- TABBED NAVIGATION (The UI Upgrade) ---
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Ledger", "📈 Analysis"])

    with tab1:
        st.subheader("Executive Overview")

        # --- 1. TOP MOVERS (Gainers & Losers) ---
        st.markdown("##### 🚀 Top Movers")

        # Sort by return to find the extremes
        sorted_df = df.sort_values(by="Return (%)", ascending=False)
        top_gainers = sorted_df.head(2)
        top_losers = sorted_df.tail(2).sort_values(by="Return (%)", ascending=True)

        tm1, tm2, tm3, tm4 = st.columns(4)

        # Safe metric rendering (in case the portfolio has fewer than 4 stocks)
        if len(top_gainers) >= 1:
            tm1.metric(f"🟢 {top_gainers.iloc[0]['Stock']}", f"₹{top_gainers.iloc[0]['Current Value']:,.0f}",
                       f"{top_gainers.iloc[0]['Return (%)']:.2f}%")
        if len(top_gainers) >= 2:
            tm2.metric(f"🟢 {top_gainers.iloc[1]['Stock']}", f"₹{top_gainers.iloc[1]['Current Value']:,.0f}",
                       f"{top_gainers.iloc[1]['Return (%)']:.2f}%")
        if len(top_losers) >= 1:
            tm3.metric(f"🔴 {top_losers.iloc[0]['Stock']}", f"₹{top_losers.iloc[0]['Current Value']:,.0f}",
                       f"{top_losers.iloc[0]['Return (%)']:.2f}%")
        if len(top_losers) >= 2:
            tm4.metric(f"🔴 {top_losers.iloc[1]['Stock']}", f"₹{top_losers.iloc[1]['Current Value']:,.0f}",
                       f"{top_losers.iloc[1]['Return (%)']:.2f}%")

        st.divider()

        # --- 2. ALLOCATION & QUANTITATIVE HEALTH ---
        col_tree, col_score = st.columns([2, 1])

        with col_tree:
            st.markdown("##### 🗺️ Sector & Asset Allocation")

            # Setup a root column for the Treemap hierarchy
            df["Portfolio"] = "Total Assets"
            fig_tree = px.treemap(
                df,
                path=['Portfolio', 'Sector', 'Stock'],
                values='Current Value',
                color='Return (%)',
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0
            )

            # Apply the transparent, premium aesthetic
            fig_tree.update_layout(
                margin=dict(t=20, l=10, r=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E2E8F0')
            )
            st.plotly_chart(fig_tree, width='stretch')

        with col_score:
            st.markdown("##### 🧠 System Vitals Score")

            # Placeholder logic: Currently calculating a simple "Win Rate" of the portfolio.
            # This is the exact spot to hook in a custom ML model or technical indicator scoring engine later.
            win_rate = (len(df[df['Return (%)'] > 0]) / len(df)) * 100 if len(df) > 0 else 0

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=win_rate,
                number={'font': {'color': '#E2E8F0', 'size': 40}, 'suffix': "/100"},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': "#38BDF8"},
                    'bgcolor': "rgba(255,255,255,0.05)",
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, 40], 'color': "rgba(248, 113, 113, 0.2)"},  # Red
                        {'range': [40, 70], 'color': "rgba(250, 204, 21, 0.2)"},  # Yellow
                        {'range': [70, 100], 'color': "rgba(52, 211, 153, 0.2)"}  # Green
                    ],
                }
            ))

            fig_gauge.update_layout(
                height=350,
                margin=dict(t=30, l=20, r=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E2E8F0')
            )
            st.plotly_chart(fig_gauge, width='stretch')

    with tab2:
        st.subheader("Holdings Detail")

        # Calculate Portfolio Weight for the visual allocation bar
        total_val = df['Current Value'].sum()
        df['Weight (%)'] = (df['Current Value'] / total_val) * 100

        # Create a fresh copy for the display table
        display_df = df[["Stock", "Sector", "Qty", "Avg Price", "Current Price", "Return (%)", "Weight (%)",
                         "Current Value"]].copy()

        # Render the upgraded interactive dataframe
        st.dataframe(
            display_df,
            column_config={
                "Stock": st.column_config.TextColumn(
                    "Ticker",
                    width="medium"
                ),
                "Sector": st.column_config.TextColumn(
                    "Sector"
                ),
                "Qty": st.column_config.NumberColumn(
                    "Quantity"
                ),
                "Avg Price": st.column_config.NumberColumn(
                    "Avg Buy",
                    format="₹%.2f"
                ),
                "Current Price": st.column_config.NumberColumn(
                    "LTP",
                    format="₹%.2f"
                ),
                "Return (%)": st.column_config.NumberColumn(
                    "Return",
                    format="%.2f%%"
                ),
                "Weight (%)": st.column_config.ProgressColumn(
                    "Allocation",
                    help="Percentage of total portfolio value",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Current Value": st.column_config.NumberColumn(
                    "Total Value",
                    format="₹%.0f"
                )
            },
            hide_index=True,
            width='stretch',
            height=400
        )

    with tab3:
        st.subheader("Technical Analysis & Momentum")
        selected_stock = st.selectbox("Select a holding:", df['Stock'].tolist())

        # 1. Isolate the data for the specific stock you selected
        stock_data = df[df['Stock'] == selected_stock].iloc[0]

        # 2. Extract the numbers
        s_invested = stock_data['Invested']
        s_current = stock_data['Current Value']
        s_abs_return = s_current - s_invested
        s_pct_return = stock_data['Return (%)']
        s_avg_price = stock_data['Avg Price']
        s_current_price = stock_data['Current Price']

        # 3. Display them in a clean row above the chart
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Avg Buy Price", f"₹{s_avg_price:,.2f}", height='stretch')
        sc2.metric("LTP (Current)", f"₹{s_current_price:,.2f}", height='stretch')
        sc3.metric("Position Return", f"₹{s_abs_return:,.0f}", f"{s_pct_return:.2f}%", height='stretch')
        sc4.metric("Position Value", f"₹{s_current:,.0f}", height='stretch')

        st.divider()

        # --- UPGRADED CHARTING ENGINE ---
        with premium_spinner(f"Loading quantitative data for {selected_stock}..."):
            # Fetch Data
            hist_data = yf.download(f"{selected_stock}.NS", period="2y", progress=False)
            if len(hist_data) == 0:
                hist_data = yf.download(f"{selected_stock}.BO", period="2y", progress=False)

            # Flatten multi-index if yfinance returns it
            if isinstance(hist_data.columns, pd.MultiIndex):
                hist_data.columns = hist_data.columns.droplevel(1)

            # Calculate SMAs
            hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
            hist_data['SMA_50'] = hist_data['Close'].rolling(window=50).mean()
            hist_data['SMA_200'] = hist_data['Close'].rolling(window=200).mean()

            # Calculate RSI (14-Day)
            delta = hist_data['Close'].diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            ema_up = up.ewm(com=13, adjust=False).mean()
            ema_down = down.ewm(com=13, adjust=False).mean()
            rs = ema_up / ema_down
            hist_data['RSI'] = 100 - (100 / (1 + rs))

            # --- BUILD SUBPLOTS ---
            fig_trend = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.6, 0.2, 0.2],
                subplot_titles=(None, "Volume Profile", "RSI (14-Day Momentum)")
            )

            # ROW 1: Price and SMAs
            fig_trend.add_trace(go.Scatter(x=hist_data.index, y=hist_data['Close'], mode='lines', name='Close',
                                           line=dict(color='#60A5FA', width=2)), row=1, col=1)
            fig_trend.add_trace(go.Scatter(x=hist_data.index, y=hist_data['SMA_20'], mode='lines', name='20 SMA',
                                           line=dict(color='#F5DD90', width=2, dash='dot')), row=1, col=1)
            fig_trend.add_trace(go.Scatter(x=hist_data.index, y=hist_data['SMA_50'], mode='lines', name='50 SMA',
                                           line=dict(color='#F87171', width=2, dash='dot')), row=1, col=1)
            fig_trend.add_trace(go.Scatter(x=hist_data.index, y=hist_data['SMA_200'], mode='lines', name='200 SMA',
                                           line=dict(color='#809848', width=2, dash='dot')), row=1, col=1)

            # ROW 2: Volume
            # Using a semi-transparent gray to match your glassmorphism theme
            fig_trend.add_trace(go.Bar(x=hist_data.index, y=hist_data['Volume'], name='Volume',
                                       marker_color='rgba(156, 163, 175, 0.4)'), row=2, col=1)

            # ROW 3: RSI
            fig_trend.add_trace(go.Scatter(x=hist_data.index, y=hist_data['RSI'], mode='lines', name='RSI',
                                           line=dict(color='#C084FC', width=2)), row=3, col=1)

            # Add Overbought/Oversold thresholds to RSI
            fig_trend.add_hline(y=70, line_dash="dash", line_color="#F87171", row=3, col=1, opacity=0.5)
            fig_trend.add_hline(y=30, line_dash="dash", line_color="#34D399", row=3, col=1, opacity=0.5)

            # Apply your premium aesthetic
            fig_trend.update_layout(
                height=700,  # Increased height to fit all three panels comfortably
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E2E8F0'),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0)
            )

            # Grid styling for all subplots
            fig_trend.update_yaxes(showgrid=True, gridcolor='#1F2937')
            fig_trend.update_xaxes(showgrid=False)

            # Restrict RSI Y-axis from 0 to 100
            fig_trend.update_yaxes(range=[0, 100], row=3, col=1)

            st.plotly_chart(fig_trend, width='stretch')