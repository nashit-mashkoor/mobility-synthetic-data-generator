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
    page_title="Synthetic Gait Data Generator", layout="wide", initial_sidebar_state="collapsed",
    page_icon='📊'
)

# Custom CSS for beautiful styling
CUSTOM_CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Hero section styling */
.hero-section {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    border: 1px solid #e94560;
    box-shadow: 0 4px 20px rgba(233, 69, 96, 0.2);
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #e94560;
    text-align: center;
    margin-bottom: 0.5rem;
}

.hero-subtitle {
    font-size: 1.1rem;
    color: #a2d2ff;
    text-align: center;
    margin-bottom: 1rem;
}

/* Stats display */
.stats-container {
    display: flex;
    justify-content: center;
    gap: 3rem;
    flex-wrap: wrap;
    margin: 1.5rem 0;
}

.stat-item {
    text-align: center;
    padding: 1rem;
}

.stat-number {
    font-size: 2.2rem;
    font-weight: 700;
    color: #e94560;
}

.stat-label {
    color: #a2d2ff;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Section headers */
.section-header {
    background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
    padding: 1rem 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #e94560;
    margin: 1.5rem 0 1rem 0;
}

.section-header h3 {
    color: #e94560;
    margin: 0;
    font-size: 1.3rem;
}

/* Info cards */
.info-card {
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid rgba(233, 69, 96, 0.2);
    margin-bottom: 1rem;
}

.info-card-title {
    color: #e94560;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.info-card-content {
    color: #ccd6f6;
    line-height: 1.7;
}

/* Phase badges */
.phase-badge {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    margin: 0.2rem;
    font-weight: 500;
}

.phase-1 { background: rgba(74, 222, 128, 0.2); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.4); }
.phase-2 { background: rgba(251, 191, 36, 0.2); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.4); }
.phase-3 { background: rgba(251, 146, 60, 0.2); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.4); }
.phase-4 { background: rgba(248, 113, 113, 0.2); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.4); }
.phase-5 { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }

/* Feature tags */
.feature-tag {
    display: inline-block;
    background: rgba(162, 210, 255, 0.15);
    color: #a2d2ff;
    padding: 0.25rem 0.6rem;
    border-radius: 15px;
    font-size: 0.8rem;
    margin: 0.15rem;
    border: 1px solid rgba(162, 210, 255, 0.3);
}

/* Current phase indicator */
.current-phase-banner {
    background: linear-gradient(90deg, #e94560 0%, #0f3460 100%);
    padding: 0.8rem 1.5rem;
    border-radius: 10px;
    text-align: center;
    margin: 1rem 0;
}

.current-phase-text {
    color: white;
    font-size: 1.2rem;
    font-weight: 600;
}

/* Divider */
.styled-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(233, 69, 96, 0.5), transparent);
    margin: 2rem 0;
}

/* Workflow steps */
.workflow-container {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin: 1.5rem 0;
}

.workflow-step {
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    min-width: 120px;
    border: 1px solid rgba(233, 69, 96, 0.2);
}

.step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    background: #e94560;
    color: white;
    border-radius: 50%;
    font-weight: bold;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}

.step-text {
    color: #ccd6f6;
    font-size: 0.85rem;
}

/* Title alignment */
#synthetic-gait-data-generator {
    text-align: center;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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
    st.title('🚶 Synthetic Gait Data Generator')

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🧬 Mobility & Gait Synthetic Data Generator</div>
    <div class="hero-subtitle">Generate realistic synthetic gait and mobility data for healthcare analytics, research, and ML model training</div>
    <div class="stats-container">
        <div class="stat-item">
            <div class="stat-number">5</div>
            <div class="stat-label">Mobility Phases</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">9</div>
            <div class="stat-label">Gait Features</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">4</div>
            <div class="stat-label">Trend Types</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">∞</div>
            <div class="stat-label">Data Points</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Start Workflow
st.markdown("""
<div class="section-header">
    <h3>🚀 Quick Start Workflow</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="workflow-container">
    <div class="workflow-step">
        <div class="step-number">1</div>
        <div class="step-text">Select Phases</div>
    </div>
    <div class="workflow-step">
        <div class="step-number">2</div>
        <div class="step-text">Configure Dates</div>
    </div>
    <div class="workflow-step">
        <div class="step-number">3</div>
        <div class="step-text">Pick Features</div>
    </div>
    <div class="workflow-step">
        <div class="step-number">4</div>
        <div class="step-text">Set Parameters</div>
    </div>
    <div class="workflow-step">
        <div class="step-number">5</div>
        <div class="step-text">Download CSV</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Expandable Details Section
with st.expander("📖 Detailed Guide & Phase Descriptions", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">🎯 Mobility Phases</div>
            <div class="info-card-content">
                <span class="phase-badge phase-1">Phase 1: Normal</span>
                <span class="phase-badge phase-2">Phase 2: Slightly Weak</span>
                <span class="phase-badge phase-3">Phase 3: Weak</span>
                <span class="phase-badge phase-4">Phase 4: Dangerously Weak</span>
                <span class="phase-badge phase-5">Phase 5: Immobile</span>
                <br><br>
                Each phase represents a distinct mobility state, allowing you to simulate patient progression or decline over time.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">📊 Available Features</div>
            <div class="info-card-content">
                <span class="feature-tag">Gait Speed</span>
                <span class="feature-tag">Step Length</span>
                <span class="feature-tag">Step Width</span>
                <span class="feature-tag">TUG Score</span>
                <span class="feature-tag">Cadence</span>
                <span class="feature-tag">Knee Flexion</span>
                <span class="feature-tag">Sitting ADL</span>
                <span class="feature-tag">Lying ADL</span>
                <span class="feature-tag">Active Hours</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">⚙️ Configuration Options</div>
            <div class="info-card-content">
                <strong>Per Phase:</strong><br>
                • Start & End Dates<br>
                • Sampling Frequency (per day)<br><br>
                <strong>Per Feature:</strong><br>
                • Value Range (Start → End)<br>
                • Distribution Space (Linear/Geometric)<br>
                • Trend Type (Nearest/Linear/Cubic/Quadratic)<br>
                • Noise Level (Standard Deviation)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">💡 Tips</div>
            <div class="info-card-content">
                • Phase intervals are <strong>left-closed</strong><br>
                • Units are not specified - use ranges to define values<br>
                • All phases must be configured before generating data<br>
                • Include timestamps for time-series analysis
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
warning_holder = st.empty()

# Sidebar styling
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #e94560; margin-bottom: 1rem;">
    <span style="font-size: 1.5rem;">⚙️</span>
    <h3 style="color: #e94560; margin: 0.5rem 0 0 0;">Configuration Panel</h3>
</div>
""", unsafe_allow_html=True)

st.sidebar.subheader('📋 Phase Selection')
final_frame_phase = st.sidebar.multiselect('🎯 Phases to include:', 
                                                ['Phase_1', 'Phase_2', 'Phase_3', 'Phase_4', 'Phase_5'],
                                                help="Select one or more mobility phases for your dataset")

st.sidebar.markdown("---")
st.sidebar.subheader('🔧 Phase Configuration')
selected_phase = st.sidebar.radio(   
    "Select phase to configure:",
    (final_frame_phase), index=0)

st.sidebar.markdown("---")
st.sidebar.subheader('📊 Feature Selection')
final_frame_features = st.sidebar.multiselect('Features to include:', 
                                                ['Gait_Speed',
                                                'Step_Length',
                                                'Step_Width',
                                                'Tug_Score',
                                                'Cadence',
                                                'Knee_Flexion',
                                                'Sitting_Adl',
                                                'Lying_Adl',
                                                'Active_Hours'],
                                                help="Select the gait/mobility features you want in your dataset")

st.sidebar.markdown("---")
st.sidebar.subheader('⏰ Timestamp Option')
include_dates = st.sidebar.checkbox('📅 Include timestamps', help="Add date column to the generated data")
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
    selected_phase_holder.markdown(f"""
    <div class="current-phase-banner">
        <span class="current-phase-text">⏲️ Currently Configuring: {current_phase.name.replace('_', ' ')}</span>
    </div>
    """, unsafe_allow_html=True)
    siderbar_selected_phase_holder.markdown(f"**🎛️ {current_phase.name.replace('_', ' ')} Settings**")

# For selected phase render features
with st.container():
    if current_phase:
        st.markdown("""
        <div class="section-header">
            <h3>⚙️ Feature Configuration</h3>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Configure the parameters for each feature in {current_phase.name.replace('_', ' ')}")
        for feature in current_phase.feature_dic:
            current_phase.feature_dic[feature].render(get_total_data_points(st.session_state[current_phase.name+'_start_date'], st.session_state[current_phase.name+'_end_date'], 
                                                    st.session_state[current_phase.name+'_frequency_per_day']),
                                                    current_phase.name)

# Download section in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader('💾 Generate Data')
download=st.sidebar.button('🚀 Generate Download Link', help="Click to generate your synthetic dataset")
if download:
    try:
        csv = generate_data(set(final_frame_features), set(final_frame_phase), 
                        [phase_1, phase_2, phase_3, phase_4, phase_5], 
                        include_dates = include_dates).to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"SyntheticGaitData_{current_date}.csv"
        linko= f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="display: inline-block; padding: 0.5rem 1rem; background: #e94560; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">📥 Download CSV</a>'
        st.sidebar.markdown(linko, unsafe_allow_html=True)
        st.sidebar.success('✅ Data generated successfully!')
    except:
        st.sidebar.error('⚠️ Please configure all included phases before generating data.')

# Footer info
st.sidebar.markdown("---")
st.sidebar.caption("🧬 Synthetic Gait Data Generator v1.0")