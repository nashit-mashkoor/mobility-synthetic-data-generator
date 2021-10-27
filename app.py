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

from util import ActiveHoursFeature, CadenceFeature, GaitFeature, KneeFlexionFeature, LyingAdlFeature, Phase, SittingAdlFeature, StepWidthFeature, StepLengthFeature, TugScoreFeature
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

@st.cache
def generate_data(include_features, include_phases, phases, include_dates=False):
    result_json = {}
    for phase in phases:
        if str(phase) in include_phases:
            for phase_feature in phase.feature_dic:
                total_data_points = get_total_data_points(st.session_state[phase.name+'_start_date'], st.session_state[phase.name+'_end_date'], 
                                                    st.session_state[phase.name+'_frequency_per_day'])
                if str(phase_feature) in include_features:
                    feature_data = phase.feature_dic[phase_feature].get_feature_data(st.session_state[str(phase)+'_'+phase_feature+'_base_start'], st.session_state[str(phase)+'_'+phase_feature+'_base_end'],
                                                                                    st.session_state[str(phase)+'_'+phase_feature+'_space'], st.session_state[str(phase)+'_'+phase_feature+'_trend'], 
                                                                                    st.session_state[str(phase)+'_'+phase_feature+'_noise'], total_data_points)[1]
                    result_json[phase_feature] = np.concatenate((result_json.get(phase_feature, []), feature_data))
            
            if include_dates:
                result_json['Date'] = np.concatenate((result_json.get('Date', np.array([],dtype='datetime64[D]')), phase.get_date_data(st.session_state[phase.name+'_start_date'], 
                                                                                                                                        st.session_state[phase.name+'_end_date'], 
                                                                                                                                        st.session_state[phase.name+'_frequency_per_day'])))
 
    result_df = pd.DataFrame(result_json)
    return result_df

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
        'Gait_Speed': GaitFeature(),
        'Step_Length': StepLengthFeature(),
        'Step_Width': StepWidthFeature(),
        'Tug_Score': TugScoreFeature(),
        'Cadence': CadenceFeature(),
        'Knee_Flexion': KneeFlexionFeature(),
        'Sitting_Adl': SittingAdlFeature(),
        'Lying_Adl': LyingAdlFeature(),
        'Active_Hours': ActiveHoursFeature()
    }
)
phase_2.add_features(
    {
        'Gait_Speed': GaitFeature(),
        'Step_Length': StepLengthFeature(),
        'Step_Width': StepWidthFeature(),
        'Tug_Score': TugScoreFeature(),
        'Cadence': CadenceFeature(),
        'Knee_Flexion': KneeFlexionFeature(),
        'Sitting_Adl': SittingAdlFeature(),
        'Lying_Adl': LyingAdlFeature(),
        'Active_Hours': ActiveHoursFeature()
        
    }
)
phase_3.add_features(
    {
        'Gait_Speed': GaitFeature(),
        'Step_Length': StepLengthFeature(),
        'Step_Width': StepWidthFeature(),
        'Tug_Score': TugScoreFeature(),
        'Cadence': CadenceFeature(),
        'Knee_Flexion': KneeFlexionFeature(),
        'Sitting_Adl': SittingAdlFeature(),
        'Lying_Adl': LyingAdlFeature(),
        'Active_Hours': ActiveHoursFeature()
        
    }
)
phase_4.add_features(
    {
        'Gait_Speed': GaitFeature(),
        'Step_Length': StepLengthFeature(),
        'Step_Width': StepWidthFeature(),
        'Tug_Score': TugScoreFeature(),
        'Cadence': CadenceFeature(),
        'Knee_Flexion': KneeFlexionFeature(),
        'Sitting_Adl': SittingAdlFeature(),
        'Lying_Adl': LyingAdlFeature(),
        'Active_Hours': ActiveHoursFeature()
    }
)
phase_5.add_features(
    {
        'Gait_Speed': GaitFeature(),
        'Step_Length': StepLengthFeature(),
        'Step_Width': StepWidthFeature(),
        'Tug_Score': TugScoreFeature(),
        'Cadence': CadenceFeature(),
        'Knee_Flexion': KneeFlexionFeature(),
        'Sitting_Adl': SittingAdlFeature(),
        'Lying_Adl': LyingAdlFeature(),
        'Active_Hours': ActiveHoursFeature()
    }
)

# App Variables
current_phase = None#phase_1
selected_phase = ''#phase_1.name

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
            2.  Select all the phases required in the final data
            3.  Description of each phase:
                * Phase 1 (Normal)
                * Phase 2 (Slightly weak)
                * Phase 3 (Weak)
                * Phase 4 (Dangerously weak)
                * Phase 5 (Immobile)
            4.  Configure the settings for the each phase 
                * The data generation link will only be activated once all phases are configured
                * Phase intervals are left closed
            5.  Select the features required in the final data
            6.  For each phase configure the settings for each feature
            7. The units of features are not specified since ranges are being used to define the values generated
                Keep in mind the assumed unit while interperating the results 
            8.  Click on generate link button to create hyper link to download the CSV file   
            """)
warning_holder = st.empty()
st.sidebar.subheader('⚙️ Sytsem Configuration:')
final_frame_phase = st.sidebar.multiselect('Add phases to include in the final frame ?', 
                                                ['Phase_1', 'Phase_2', 'Phase_3', 'Phase_4', 'Phase_5'])
selected_phase = st.sidebar.radio(   
    "Select the phase to configure",
    (final_frame_phase), index=0)
final_frame_features = st.sidebar.multiselect('Select the features to include in the final frame ?', 
                                                ['Gait_Speed',
                                                'Step_Length',
                                                'Step_Width',
                                                'Tug_Score',
                                                'Cadence',
                                                'Knee_Flexion',
                                                'Sitting_Adl',
                                                'Lying_Adl',
                                                'Active_Hours'])
include_dates = st.sidebar.checkbox('Include time stamps in final frame')
selected_phase_holder = st.empty()
siderbar_selected_phase_holder = st.sidebar.empty()
phase_configure_place_holder = st.empty()

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
if current_phase:
    current_phase.render_config()
# Render placeholders
if current_phase:
    selected_phase_holder.header('⏲️ Current Phase:  **{}**'.format(current_phase.name))
    siderbar_selected_phase_holder.subheader("⚙️ {} configuration".format(current_phase.name))

# For selected phase render features
with st.container():
    if current_phase:
        st.header('⚙️ Feature Configuration:')
        for feature in current_phase.feature_dic:
            current_phase.feature_dic[feature].render(get_total_data_points(st.session_state[current_phase.name+'_start_date'], st.session_state[current_phase.name+'_end_date'], 
                                                    st.session_state[current_phase.name+'_frequency_per_day']),
                                                    current_phase.name)
download=st.sidebar.button('Generate Download Link!')
if download:
    try:
        csv = generate_data(set(final_frame_features), set(final_frame_phase), 
                        [phase_1, phase_2, phase_3, phase_4, phase_5], 
                        include_dates = include_dates).to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings
        linko= f'<a href="data:file/csv;base64,{b64}" download="Data.csv">Download csv file</a>'
        st.sidebar.markdown(linko, unsafe_allow_html=True)
    except:
        st.sidebar.error('Configure all included phases to generate download link....')