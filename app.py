import sys
import numpy as np
import pandas as pd
import datetime
import streamlit as st
import plotly.express as px
import pylab
import altair as alt
import functools
import base64
import random
import scipy.interpolate

from util import GaitFeature, StepFeature, Phase
from contextlib import contextmanager
from io import StringIO
from streamlit.report_thread import REPORT_CONTEXT_ATTR_NAME
from threading import current_thread

@st.cache
def get_total_data_points(start, end, freq):
    return ((end - start) * freq).days

@st.cache
def get_feature_data(start, end, space, trend, noise, total_points):
    # The len of the values that are generated using numpy
    if total_points < 10:
        initial_space_len =  total_points
    else:
        initial_space_len =  total_points // 10

    # Create Random noise distribution, where std selected by user
    if noise != 0:
        noise = np.random.normal(0, noise, initial_space_len)

    if space == 'Linear':
        y = np.linspace(start, end, initial_space_len) + noise
    else:
        y = np.geomspace(start, end, initial_space_len) + noise

    x = np.linspace(0, initial_space_len, initial_space_len)
    
    #use finer and regular mesh for plot
    xfine = np.linspace(0, initial_space_len, total_points)

    if trend == 'Nearest':
        #interpolate with piecewise nearest function (p=0)
        y = (scipy.interpolate.interp1d(x, y, kind='nearest')(xfine))  
    elif trend == 'Linear':
        #interpolate with piecewise linear func (p=1)
        y = (scipy.interpolate.interp1d(x, y, kind='linear')(xfine)) 
    elif trend == 'Cubic':
        #interpolate with piecewise cubic func (p=2)
        y = (scipy.interpolate.interp1d(x, y, kind='cubic')(xfine)) 
    else:    
        #interpolate with piecewise qudratic func (p=2) with additional noise
        y = (scipy.interpolate.interp1d(x, y, kind='quadratic')(xfine)) + np.random.normal(0, (abs(start - end)) / 2, total_points)
    return xfine, y

@st.cache
def get_date_data(start, end, freq):
    step = datetime.timedelta(days=1 / freq)
    result = []
    while start < end:
        result.append(start)
        start += step
    return result

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'
    return href

# App setting
st.set_page_config(
    page_title="Data Generator", layout="wide", initial_sidebar_state="collapsed",
    page_icon='💽'
)
HIDE_STREAMLIT_STYLE = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)

# Initialise phases
phase_1 = Phase('Phase_1')
phase_2 = Phase('Phase_2')
phase_3 = Phase('Phase_3')
phase_4 = Phase('Phase_4')
phase_5 = Phase('Phase_5')

# Append reuired features to each phase
phase_1.add_features(
    {
        'Gait Speed': GaitFeature(start_default=0.6, end_default=0.8, noise_min=0.0, noise_max=1.0, noise_step=0.05, noise_default=0.0),
        'Step Speed': StepFeature(start_default=0.6, end_default=0.8, noise_min=0.0, noise_max=1.0, noise_step=0.05, noise_default=0.0),

    }
)
phase_2.add_features(
    {
        'Gait Speed': GaitFeature(start_default=0.6, end_default=0.8, noise_min=0.0, noise_max=1.0, noise_step=0.05, noise_default=0.0),
        
    }
)
phase_3.add_features(
    {
        'Gait Speed': GaitFeature(start_default=0.6, end_default=0.8, noise_min=0.0, noise_max=1.0, noise_step=0.05, noise_default=0.0),
        
    }
)
phase_4.add_features(
    {
        'Gait Speed': GaitFeature(start_default=0.6, end_default=0.8, noise_min=0.0, noise_max=1.0, noise_step=0.05, noise_default=0.0),
        
    }
)
phase_5.add_features(
    {
        'Gait Speed': GaitFeature(start_default=0.6, end_default=0.8, noise_min=0.0, noise_max=1.0, noise_step=0.05, noise_default=0.0),
        
    }
)
# App Variables
current_phase = phase_1
selected_phase = phase_1.name

with st.container():
    st.title('🛢️ Synthetic Data Generator')
    TITLE_ALIGNMENT="""
                    <style>
                    #synthetic-data-generator {
                    text-align: center
                    }
                    </style>
                    """
    st.markdown(TITLE_ALIGNMENT, unsafe_allow_html=True)
                
with st.container():
    st.header('🔍System Description:')
    st.info(f"""  
            1.  The platform has been desgined to create synthetic data gneration for personicle trend analysis
            2.  Select the phase to configure from the side bar
            3.  Description of each phase:
                * Phase 1 (Normal)
                * Phase 2 (Slightly weak)
                * Phase 3 (Weak)
                * Phase 4 (Dangerously weak)
                * Phase 5 (Immobile)
            4.  Configure the settings for the phase selected 
            5.  For each phase configure the settings for each feature
            6.  Once satisified download the CSV file   
            """)

st.sidebar.subheader('⚙️ Sytem Configuration:')
if st.sidebar.checkbox('Change Phase'):
    selected_phase = st.sidebar.radio(   
        "Select from the following phase",
        ('Phase_1', 'Phase_2', 'Phase_3', 'Phase_4', 'Phase_5'),
        index = 0)
include_dates = st.sidebar.checkbox('Include time stamps in final frame')
selected_phase_holder = st.empty()
siderbar_selected_phase_holder = st.sidebar.empty()

# Update current phase
if selected_phase == 'Phase_1':
    current_phase = phase_1
elif selected_phase == 'Phase_2':
    current_phase = phase_2
elif selected_phase == 'Phase_3':
    current_phase = phase_3
elif selected_phase == 'Phase_4':
    current_phase = phase_4
elif selected_phase == 'Phase_5':
    current_phase = phase_5

# Render phase config in sub header
current_phase.render_config()
st.sidebar.button('Generate Data')

# Render placeholders
selected_phase_holder.header('⏲️ Current Phase:  **{}**'.format(current_phase.name))
siderbar_selected_phase_holder.subheader("⚙️ {} configuration".format(current_phase.name))

# For selected phase render features
with st.container():
    st.header('⚙️ Feature Configuration:')
    for feature in current_phase.feature_dic:
        current_phase.feature_dic[feature].render(get_total_data_points(st.session_state[current_phase.name+'_start_date'], st.session_state[current_phase.name+'_end_date'], 
                                                st.session_state[current_phase.name+'_frequency_per_day']),
                                                current_phase.name)