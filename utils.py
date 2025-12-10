import pandas as pd
import streamlit as st

def get_post_stats(history):
    if not history:
        return 0, 0, 0
    df = pd.DataFrame(history)
    total = len(df)
    success = len(df[df['Status'] == 'Success'])
    failed = len(df[df['Status'] == 'Failed'])
    return total, success, failed

def prepare_chart_data(history):
    if not history:
        return pd.DataFrame()
    df = pd.DataFrame(history)
    # Convert Time to datetime
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'])
        df['Date'] = df['Time'].dt.date
        counts = df.groupby('Date').size()
        return counts
    return pd.DataFrame()
