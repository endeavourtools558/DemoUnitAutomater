import streamlit as st
from Demounit_report_scrapper import Run_Demounit_report_scrapper
from Demo_Unit_Automater import Run_Demo_Unit_Automater
## Libraries
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
from io import BytesIO
from datetime import datetime
import streamlit as st
import pandas as pd
from datetime import timedelta
import plotly.express as px


head1, head2 = st.columns([2,5])

with head2:
    ##HEADLINE
    st.title('ET2608 DEMO UNIT TOOL')

with head1:
    st.image("Endeavour_Tools_Logo.png", width=150)

sharepoint_link = "https://endeavourtools.sharepoint.com/:x:/s/TechnicalSupport/EdmAB-6Te6RFvLXTOe5MS_ABCzJLxMqbDY0U4f9nTvuxFg?download=1"

st.markdown(f"[Open Excel File in SharePoint]({sharepoint_link})", unsafe_allow_html=True)


uploaded_file = st.file_uploader("📁 Upload Master Demo Unit Data", type=["xlsx"])

tab1, tab2 = st.tabs(["📊 Demo Unit Report Scrapper", "⚙️ Demo Unit Automater"])


with tab1:
    Run_Demounit_report_scrapper(uploaded_file)

with tab2:
    Run_Demo_Unit_Automater(uploaded_file)