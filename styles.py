import streamlit as st


def apply_custom_css():
    st.markdown("""
    <style>
        /* Modern Dark Gradient Background */
        #MainMenu {
            background: rgba(20, 30, 48, 0.85);
            backdrop-filter: blur(15px);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        header {
            background: rgba(20, 30, 48, 0.85) !important; 
            backdrop-filter: blur(15px)!important;
        }
        footer {visibility: hidden;}
        .stApp {
            background: linear-gradient(135deg, #141e30 0%, #243b55 100%);
            color: white;
        }

        /* Softer Frosted Glass for Metrics and Containers */
        [data-testid="stMetric"], .css-1r6slb0, .css-12oz5g7 {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 20px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);\
        }

        /* Style the Tabs to look like buttons */
        [data-testid="stTabs"] button {
            background-color: rgba(255,255,255,0.05);
            border-radius: 8px 8px 0px 0px;
            border: 1px solid rgba(255,255,255,0.1);
            border-bottom: none;
            padding: 1rem;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            background-color: rgba(255,255,255,0.15);
            border-bottom: 2px solid #00f2fe;
        }

        /* Force text colors */
        h1, h2, h3, p, span, div {
            color: #e2e8f0 !important;
        }

        /* Glassmorphism Sidebar */
        [data-testid="stSidebar"] {
            background: rgba(20, 30, 48, 0.85);
            backdrop-filter: blur(15px);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        .custom-loader-container {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin: 1rem 0;
        }
        
        .custom-loader {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255, 255, 255, 0.05);
            border-radius: 50%;
            /* The glowing accent color matching your tab underline */
            border-top-color: #00f2fe; 
            animation: smooth-spin 1s cubic-bezier(0.4, 0, 0.2, 1) infinite;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
        }
        
        @keyframes smooth-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .custom-loader-text {
            margin-top: 1rem;
            color: #9CA3AF;
            font-size: 0.9rem;
            font-weight: 500;
            letter-spacing: 0.5px;
        }
    </style>
    """, unsafe_allow_html=True)