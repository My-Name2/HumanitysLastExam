import streamlit as st
from datasets import load_dataset
from huggingface_hub import login
import random

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Humanity's Last Exam",
    page_icon="🧠",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0f;
    color: #e8e6e0;
}

h1, h2, h3 { font-family: 'Playfair Display', serif; }

.stApp { background-color: #0a0a0f; }

/* Header */
.hle-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    border-bottom: 1px solid #2a2a3a;
    margin-bottom: 2rem;
}
.hle-header h1 {
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: -1px;
    color: #f5f0e8;
    margin: 0;
}
.hle-header .subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #666;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* Question card */
.q-card {
    background: #13131f;
    border: 1px solid #2a2a3a;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    position: relative;
}
.q-card:hover { border-color: #c8a96e; transition: border-color 0.2s; }

.q-number {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #c8a96e;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}
.q-subject {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #888;
    background: #1e1e2e;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 1rem;
}
.q-text {
    font-size: 1.05rem;
    line-height: 1.7;
    color: #ddd8cc;
    margin-bottom: 1.25rem;
}
.q-type-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    padding: 3px 8px;
    border-radius: 4px;
    background: #1a2a1a;
    color: #6aaa6a;
    border: 1px solid #2a4a2a;
    margin-bottom: 1rem;
    display: inline-block;
}
.answer-box {
    background: #0d1a0d;
    border: 1px solid #2a4a2a;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem;
    color: #7acc7a;
    margin-top: 1rem;
}
.answer-label {
    font-size: 0.65rem;
    color: #4a7a4a;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}

/* Stats bar */
.stats-bar {
    display: flex;
    gap: 2rem;
    background: #13131f;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: #888;
}
.stat-item span { color: #c8a96e; font-size: 1.1rem; font-weight: 500; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d0d18 !important;
    border-right: 1px solid #2a2a3a;
}

/* Buttons */
.stButton > button {
    background: #1e1e2e !important;
    color: #c8a96e !important;
    border: 1px solid #c8a96e !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #c8a96e !important;
    color: #0a0a0f !important;
}

/* Selectbox / input */
.stSelectbox label, .stTextInput label, .stNumberInput label, .stSlider label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    color: #888 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

div[data-testid="stMetric"] {
    background: #13131f;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    padding: 1rem;
}
div[data-testid="stMetric"] label { color: #888 !important; font-family: 'DM Mono', monospace !important; font-size: 0.7rem !important; }
div[data-testid="stMetric"] div { color: #c8a96e !important; font-family: 'Playfair Display', serif !important; }

hr { border-color: #2a2a3a !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hle-header">
    <h1>Humanity's Last Exam</h1>
    <div class="subtitle">2,500 questions · expert-vetted · frontier benchmark</div>
</div>
""", unsafe_allow_html=True)

# ── Auth / Load ───────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading dataset from Hugging Face...")
def load_hle(token):
    login(token=token)
    return load_dataset("cais/hle", split="test")

hf_token = st.secrets["HF_TOKEN"]

with st.sidebar:

    dataset = load_hle(hf_token)

    st.markdown("---")
    st.markdown("### 🔍 Filters")

    subjects = sorted(set(ex.get("subject", "Unknown") or "Unknown" for ex in dataset))
    subject_filter = st.selectbox("Subject", ["All"] + subjects)

    answer_types = sorted(set(ex.get("answer_type", "Unknown") or "Unknown" for ex in dataset))
    type_filter = st.selectbox("Answer Type", ["All"] + answer_types)

    show_answers = st.toggle("Show Answers", value=False)

    st.markdown("---")
    st.markdown("### 🎲 Navigation")
    if st.button("Random Question"):
        st.session_state.random_idx = random.randint(0, len(dataset) - 1)
        st.session_state.page = 0

# ── Filter dataset ────────────────────────────────────────────────────────────
filtered = [
    (i, ex) for i, ex in enumerate(dataset)
    if (subject_filter == "All" or (ex.get("subject") or "Unknown") == subject_filter)
    and (type_filter == "All" or (ex.get("answer_type") or "Unknown") == type_filter)
]

# ── Stats ─────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Questions", f"{len(dataset):,}")
with col2:
    st.metric("Filtered", f"{len(filtered):,}")
with col3:
    st.metric("Subjects", len(subjects))
with col4:
    multi = sum(1 for ex in dataset if ex.get("answer_type") == "multipleChoice")
    st.metric("Multiple Choice", f"{multi:,}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Pagination ────────────────────────────────────────────────────────────────
PER_PAGE = 10

if "page" not in st.session_state:
    st.session_state.page = 0

# Handle random jump
if "random_idx" in st.session_state:
    # Find this index in filtered
    for pos, (orig_i, _) in enumerate(filtered):
        if orig_i == st.session_state.random_idx:
            st.session_state.page = pos // PER_PAGE
            break
    del st.session_state.random_idx

total_pages = max(1, (len(filtered) - 1) // PER_PAGE + 1)
st.session_state.page = min(st.session_state.page, total_pages - 1)

page_start = st.session_state.page * PER_PAGE
page_items = filtered[page_start: page_start + PER_PAGE]

# ── Render questions ──────────────────────────────────────────────────────────
if not filtered:
    st.info("No questions match your filters.")
else:
    for orig_i, ex in page_items:
        subject = ex.get("subject") or "Unknown"
        q_text = ex.get("question", "")
        answer = ex.get("answer", "")
        answer_type = ex.get("answer_type") or "unknown"
        choices = ex.get("answer_choices") or []

        answer_section = ""
        if show_answers:
            answer_section = f"""
            <div class="answer-box">
                <div class="answer-label">Answer</div>
                {answer}
            </div>"""

        choices_html = ""
        if answer_type == "multipleChoice" and choices:
            choices_html = "<div style='margin: 0.75rem 0; font-size:0.9rem; color:#bbb;'>"
            for c in choices:
                choices_html += f"<div style='padding:3px 0'>▸ {c}</div>"
            choices_html += "</div>"

        st.markdown(f"""
        <div class="q-card">
            <div class="q-number">Question #{orig_i + 1}</div>
            <span class="q-subject">{subject}</span>
            <span class="q-type-badge">{answer_type}</span>
            <div class="q-text">{q_text}</div>
            {choices_html}
            {answer_section}
        </div>
        """, unsafe_allow_html=True)

    # ── Pagination controls ───────────────────────────────────────────────────
    st.markdown("---")
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("← Previous", disabled=st.session_state.page == 0):
            st.session_state.page -= 1
            st.rerun()
    with col_info:
        st.markdown(
            f"<div style='text-align:center; font-family: DM Mono, monospace; font-size:0.8rem; color:#888; padding-top:0.5rem'>"
            f"Page {st.session_state.page + 1} of {total_pages} &nbsp;·&nbsp; "
            f"Q {page_start + 1}–{min(page_start + PER_PAGE, len(filtered))} of {len(filtered)}"
            f"</div>",
            unsafe_allow_html=True
        )
    with col_next:
        if st.button("Next →", disabled=st.session_state.page >= total_pages - 1):
            st.session_state.page += 1
            st.rerun()
