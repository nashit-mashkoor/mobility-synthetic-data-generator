import streamlit as st
import numpy as np
import scipy.interpolate
import datetime
import pandas as pd
import plotly.express as px

class Phase:
    def __init__(self, name, feature_dic={}):
        self.name = name
        self.feature_dic = feature_dic

    def add_feature(self, feature):
        self.feature_dic[str(feature)] = feature

    def add_features(self, feature_dic):
        self.feature_dic = feature_dic
    @st.cache
    def get_total_data_points(self, start, end, freq):
        return ((end - start) * freq).days

    @st.cache
    def get_date_data(self, start, end, freq):
        step = datetime.timedelta(days=1 / freq)
        result = []
        while start < end:
            result.append(start)
            start += step
        return result

    def render_config(self):
        start_date = st.sidebar.date_input(
                "Phase Start date", datetime.date(2021, 9, 21), min_value=datetime.date(2000, 1, 1), key=self.name + '_start_date'
            )
        end_date = st.sidebar.date_input(
                "Phase End date", datetime.date(2021, 10, 21), min_value=start_date, key=self.name+'_end_date'
            )
        frequency_per_day = st.sidebar.number_input("Frequency per day", value=1, format="%d", key=self.name + '_frequency_per_day')


class BaseFeature:
    def render(self, total_data_points, phase_name):
        pass
    
    @st.cache
    def get_feature_data(self, start, end, space, trend, noise, total_points):
    
        # The len of the values that are generated using numpy
        if (total_points // 10) < 10:
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


class GaitFeature(BaseFeature):
    def __init__(self, start_default=0.6, end_default=0.8, noise_min=0.0, noise_max=1.0, noise_step=0.05, noise_default=0.0):
        self.start_default = start_default
        self.end_default = end_default
        self.noise_min = noise_min
        self.noise_max = noise_max
        self.noise_step = noise_step
        self.noise_default = noise_default

    def render(self, total_data_points, phase_name):
        feature_name = self.__str__()
        with st.expander(feature_name):
            feature_start_base = st.number_input("Feature Base start value", value=self.start_default, 
                                                format="%f", key=phase_name+'_'+feature_name+'_base_start')
            feature_end_base = st.number_input("Feature Base end value", value=self.end_default, 
                                                format="%f", key=phase_name+'_'+feature_name+'_base_end')
            feature_space = st.radio('Select feature space', ['Linear', 'Geometric'], 
                                    key=phase_name+'_'+feature_name+'_space')
            feature_trend = st.radio('Select feature trend', ['Nearest', 'Linear', 'Cubic', 'Quadratic'],
                                     key=phase_name+'_'+feature_name+'_trend')
            feature_noise = st.slider('Select Noise to add', min_value=self.noise_min, max_value=self.noise_max, 
                                            value=self.noise_default, step=self.noise_step, 
                                            key=phase_name+'_'+feature_name+'_noise')
            if st.checkbox("📈 Visualise Data", key=phase_name+'_'+feature_name+'_visualise'):
                with st.spinner('Processing feature ....'):
                    if total_data_points > 0:
                        feature_data = self.get_feature_data(feature_start_base, feature_end_base, feature_space, 
                                                feature_trend, feature_noise, total_data_points)
                        feature_data_df = pd.DataFrame( feature_data[1], columns=['Gait_Speed'], index=feature_data[0], dtype='float64')
                        st.plotly_chart(px.line(x=list(feature_data_df.index), y=feature_data_df['Gait_Speed'], title='Gait Speed Data'),
                                        render_mode='auto', use_container_width=True, key=phase_name+'_'+feature_name+'_visualiser')
                    else:
                        st.warning('Number of data points not specified')
    
    def __str__(self):
        return 'Gait_Speed'

class StepFeature(BaseFeature):
    def __init__(self, start_default=0.6, end_default=0.8, noise_min=0.0, noise_max=1.0, noise_step=0.05, noise_default=0.0):
        self.start_default = start_default
        self.end_default = end_default
        self.noise_min = noise_min
        self.noise_max = noise_max
        self.noise_step = noise_step
        self.noise_default = noise_default

    def render(self, total_data_points, phase_name):
        feature_name = self.__str__()
        with st.expander(feature_name):
            feature_start_base = st.number_input("Feature Base start value", value=self.start_default, 
                                                format="%f", key=phase_name+'_'+feature_name+'_base_start')
            feature_end_base = st.number_input("Feature Base end value", value=self.end_default, 
                                                format="%f", key=phase_name+'_'+feature_name+'_base_end')
            feature_space = st.radio('Select feature space', ['Linear', 'Geometric'], 
                                    key=phase_name+'_'+feature_name+'_space')
            feature_trend = st.radio('Select feature trend', ['Nearest', 'Linear', 'Cubic', 'Quadratic'],
                                     key=phase_name+'_'+feature_name+'_trend')
            feature_noise = st.slider('Select Noise to add', min_value=self.noise_min, max_value=self.noise_max, 
                                            value=self.noise_default, step=self.noise_step, 
                                            key=phase_name+'_'+feature_name+'_noise')
            if st.checkbox("📈 Visualise Data", key=phase_name+'_'+feature_name+'_visualise'):
                with st.spinner('Processing feature ....'):
                    if total_data_points > 0:
                        feature_data = self.get_feature_data(feature_start_base, feature_end_base, feature_space, 
                                                feature_trend, feature_noise, total_data_points)
                        feature_data_df = pd.DataFrame( feature_data[1], columns=['Gait_Speed'], index=feature_data[0], dtype='float64')
                        st.plotly_chart(px.line(x=list(feature_data_df.index), y=feature_data_df['Gait_Speed'], title='Gait Speed Data'),
                                        render_mode='auto', use_container_width=True, key=phase_name+'_'+feature_name+'_visualiser')
                    else:
                        st.warning('Number of data points not specified')
    
    def __str__(self):
        return 'Step_Speed'
    