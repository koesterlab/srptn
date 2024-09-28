import os
from pathlib import Path

import streamlit as st
import yaml


@st.cache_resource
def config():
    with Path(os.environ["SRPTN_CONFIG"]).open("r") as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
