import os
from pathlib import Path

import streamlit as st
import yaml


@st.cache_resource
def config():
    with Path.open(os.environ["SRPTN_CONFIG"], "r") as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
