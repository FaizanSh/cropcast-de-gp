import streamlit as st
from kaggle_streamlit import kaggle_streamlit
from app import weatherAPI_Streamlit 

st.set_page_config(page_title="Weather Forecast", layout="wide")
st.sidebar.title("Choose an App")
choice = st.sidebar.radio("Select an app", ["Weather Forecast", "Data Analytics"])

if choice == "Weather Forecast":
    weatherAPI_Streamlit()
elif choice == "Data Analytics":
    kaggle_streamlit()