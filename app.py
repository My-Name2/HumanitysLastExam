import streamlit as st
from datasets import load_dataset

st.title("HLE Token Test")

try:
    token = st.secrets["HF_TOKEN"]
    st.success(f"Token found: {token[:8]}...")

    with st.spinner("Loading dataset..."):
        dataset = load_dataset("cais/hle", split="test", token=token)

    st.success(f"Dataset loaded! {len(dataset)} questions.")

except Exception as e:
    st.error(f"Error: {e}")
