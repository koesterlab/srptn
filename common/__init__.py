import os

import yaml
import streamlit as st


st.cache_resource
def config():
    with open(os.environ["SRPTN_CONFIG"], "r") as f:
        return yaml.load(f, Loader=yaml.SafeLoader)