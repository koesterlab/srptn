import streamlit as st
from streamlit_sortables import sort_items

def select_items(items=None, id=None):
    if items is None:
        items = [
            "results/diff/t3.svg",
            "results/diff/t4.svg",
        ]
    return st.multiselect(
        "Select figure items",
        items,
        label_visibility="collapsed",
        key=id,
    )


st.text("Select or upload figure items")
input_files = select_items()

if input_files:
    col1, col2 = st.columns(2)
    with col1:
        st.text("Order figure items")
        sorted_files = sort_items(input_files)

    scaled = {}
    def scaled_items():
        return {f for subset in scaled for f in subset}
    def unscaled_items():
        return [f for f in input_files if f not in scaled_items()]

    with col2:
        st.text("Scale figure items")

        def scale(i=0):
            unscaled = unscaled_items()
            if not unscaled:
                return
            selected = st.multiselect(
                "",
                options=unscaled,
                label_visibility="collapsed",
                key=f"scale-select-remaining-{i}",
            )
            if selected:
                scaled[tuple(selected)] = st.slider(
                    ",".join(selected),
                    value=1.0,
                    min_value=0.0,
                    max_value=1.0,
                    label_visibility="collapsed",
                )
                scale(i=i + 1)

        scale()

col1, col2, col3, col4 = st.columns([0.2, 0.12, 0.1, 0.58], vertical_alignment="bottom")

with col1:
    st.button("Annotate", type="primary")

with col2:
    # options are square, circle, dot, triangle
    shape = st.selectbox("Shape", options=["■", "●", "▲", "·"])

with col3:
    color = st.color_picker("Color", value="#888E88")

with col4:
    text = st.text_input("Text")

st.divider()