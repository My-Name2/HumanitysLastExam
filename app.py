import re
import random
import streamlit as st
import streamlit.components.v1 as components
from datasets import load_dataset


@st.cache_resource(show_spinner="Loading dataset...")
def load_hle(token):
    return load_dataset("cais/hle", split="test", token=token)


@st.cache_data(show_spinner=False)
def get_indices(_dataset):
    all_idx = list(range(len(_dataset)))
    mc = [i for i in all_idx if _dataset[i].get("answer_type") == "multipleChoice"]
    em = [i for i in all_idx if _dataset[i].get("answer_type") == "exactMatch"]
    return all_idx, mc, em


def format_q_text(q_text):
    return re.sub(
        r'```(.*?)```',
        r'<pre style="background:#f4f0e8;border:1px solid #e0dbd0;border-radius:6px;padding:0.75rem;font-size:0.82rem;overflow-x:auto;white-space:pre-wrap;font-family:monospace;">\1</pre>',
        q_text, flags=re.DOTALL
    )


def split_question_and_choices(ex):
    """Split question text into (question_body, choices_html) at 'Answer Choices:'."""
    q = ex.get("question", "")
    match = re.search(r'\s*Answer Choices:\s*', q, re.IGNORECASE)
    if not match:
        return format_q_text(q), ""

    body = format_q_text(q[:match.start()].strip())
    choices_raw = q[match.end():].strip()

    # Match any single uppercase letter followed by ". " at word boundary
    # e.g. A. B. C. ... Z. — handles questions with more than 5 choices
    positions = [(m.start(), m.group(1)) for m in re.finditer(r'(?:^|(?<=\s))([A-Z])\. ', choices_raw)]
    if not positions:
        choices_html = f'<div style="margin-top:0.75rem;padding:0.75rem 1rem;background:#faf8f4;border:1px solid #e8e2d8;border-radius:8px;font-size:0.95rem;color:#333;">{choices_raw}</div>'
        return body, choices_html

    choices_html = '<div style="margin-top:1rem;display:flex;flex-direction:column;gap:6px;">'
    for i, (pos, label) in enumerate(positions):
        start = pos + 3  # skip "X. "
        end = positions[i + 1][0] if i + 1 < len(positions) else len(choices_raw)
        text = choices_raw[start:end].strip()
        choices_html += f'<div style="padding:8px 14px;background:#faf8f4;border:1px solid #e8e2d8;border-radius:8px;font-size:0.95rem;color:#333;"><strong>{label}.</strong> {text}</div>'
    choices_html += '</div>'
    return body, choices_html


def get_image_html(ex):
    img_data = ex.get("image")
    if img_data:
        if not img_data.startswith("data:"):
            img_data = f"data:image/jpeg;base64,{img_data}"
        return f'<div style="margin-bottom:1rem;"><img src="{img_data}" style="max-width:100%;border-radius:8px;border:1px solid #e0dbd0;" /></div>'
    return ""


def render_page(indices, show_set):
    """Render a page of questions as a single iframe with MathJax and click-to-reveal answers."""
    cards = ""
    for orig_i in indices:
        ex = dataset[orig_i]
        subject = ex.get("subject") or "Unknown"
        q_body, choices_html = split_question_and_choices(ex)
        answer = ex.get("answer", "").replace("'", "&#39;").replace('"', "&quot;")
        answer_type = ex.get("answer_type") or "unknown"
        image_html = get_image_html(ex)

        cards += f"""
        <div class="q-card">
            <div class="q-meta">
                <span class="q-number">Question #{orig_i + 1}</span>
                <span class="q-subject">{subject}</span>
                <span class="q-type">{answer_type}</span>
            </div>
            {image_html}
            <div class="q-text">{q_body}</div>
            {choices_html}
            <div class="spoiler" onclick="this.classList.toggle('revealed')">
                <span class="spoiler-label">👁 Reveal Answer</span>
                <span class="spoiler-answer">{answer}</span>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html><head>
<script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}}}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
body {{ background:#f7f5f0; margin:0; padding:6px; font-family:'DM Sans',sans-serif; }}

.q-card {{
    background:#fff;
    border:1px solid #e0dbd0;
    border-radius:12px;
    padding:1.5rem;
    margin-bottom:1.25rem;
}}

.q-meta {{
    display:flex;
    align-items:center;
    gap:8px;
    margin-bottom:0.75rem;
    flex-wrap:wrap;
}}
.q-number {{
    font-family:'DM Mono',monospace;
    font-size:0.65rem;
    color:#8a6a2a;
    letter-spacing:2px;
    text-transform:uppercase;
}}
.q-subject {{
    font-family:'DM Mono',monospace;
    font-size:0.65rem;
    color:#999;
    background:#f0ece4;
    padding:2px 10px;
    border-radius:20px;
}}
.q-type {{
    font-family:'DM Mono',monospace;
    font-size:0.65rem;
    color:#4a8a4a;
    background:#f0f7f0;
    border:1px solid #c0dcc0;
    padding:2px 8px;
    border-radius:4px;
}}

.q-text {{
    font-size:1rem;
    line-height:1.75;
    color:#2a2a2a;
    margin-bottom:1.25rem;
}}

.spoiler {{
    display:inline-flex;
    align-items:center;
    gap:10px;
    cursor:pointer;
    padding:8px 16px;
    background:#f7f5f0;
    border:1px solid #e0dbd0;
    border-radius:8px;
    user-select:none;
    transition:background 0.2s;
}}
.spoiler:hover {{ background:#eeeae2; }}

.spoiler-label {{
    font-family:'DM Mono',monospace;
    font-size:0.75rem;
    color:#8a6a2a;
    letter-spacing:1px;
    white-space:nowrap;
}}

.spoiler-answer {{
    font-family:'DM Mono',monospace;
    font-size:0.9rem;
    color:#2a6a2a;
    filter:blur(6px);
    transition:filter 0.3s;
    max-width:600px;
}}

.spoiler.revealed .spoiler-answer {{ filter:blur(0); }}
.spoiler.revealed .spoiler-label {{ color:#4a8a4a; }}
</style>
</head>
<body>{cards}</body></html>"""

    components.html(html, height=len(indices) * 340, scrolling=True)


# ── App ───────────────────────────────────────────────────────────────────────
token = st.secrets["HF_TOKEN"]
dataset = load_hle(token)
all_indices, mc_indices, em_indices = get_indices(dataset)

st.set_page_config(page_title="Humanity's Last Exam", page_icon="🧠", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #f7f5f0; color: #1a1a1a; }
h1, h2, h3 { font-family: 'Playfair Display', serif; }
.stApp { background-color: #f7f5f0; }
.hle-header { text-align: center; padding: 2.5rem 0 1.5rem; border-bottom: 2px solid #e0dbd0; margin-bottom: 2rem; }
.hle-header h1 { font-size: 3rem; font-weight: 900; letter-spacing: -1px; color: #1a1a1a; margin: 0; }
.hle-header .subtitle { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #999; letter-spacing: 3px; text-transform: uppercase; margin-top: 0.5rem; }
section[data-testid="stSidebar"] { background: #eeeae2 !important; border-right: 1px solid #e0dbd0; }
.stButton > button { background: #fff !important; color: #8a6a2a !important; border: 1px solid #c8a96e !important; border-radius: 8px !important; font-family: 'DM Mono', monospace !important; font-size: 0.8rem !important; letter-spacing: 1px !important; }
.stButton > button:hover { background: #c8a96e !important; color: #fff !important; }
.stSelectbox label, .stRadio > label { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; color: #666 !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
div[data-testid="stMetric"] { background: #fff; border: 1px solid #e0dbd0; border-radius: 10px; padding: 1rem; }
div[data-testid="stMetric"] label { color: #999 !important; font-family: 'DM Mono', monospace !important; font-size: 0.7rem !important; }
div[data-testid="stMetric"] div { color: #8a6a2a !important; font-family: 'Playfair Display', serif !important; }
hr { border-color: #e0dbd0 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hle-header">
    <h1>Humanity's Last Exam</h1>
    <div class="subtitle">2,500 questions · expert-vetted · frontier benchmark</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔍 Filter")
    type_filter = st.selectbox("Question Type", ["All", "multipleChoice", "exactMatch"])
    st.markdown("---")
    if st.button("🎲 Random Page"):
        st.session_state.page = random.randint(0, 249)
        st.rerun()

# Filter
if type_filter == "All":
    filtered = all_indices
elif type_filter == "multipleChoice":
    filtered = mc_indices
else:
    filtered = em_indices

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total", f"{len(dataset):,}")
with col2:
    st.metric("Showing", f"{len(filtered):,}")
with col3:
    st.metric("Multiple Choice", f"{len(mc_indices):,}")

st.markdown("<br>", unsafe_allow_html=True)

PER_PAGE = 10
if "page" not in st.session_state:
    st.session_state.page = 0

total_pages = max(1, (len(filtered) - 1) // PER_PAGE + 1)
st.session_state.page = min(st.session_state.page, total_pages - 1)
page_start = st.session_state.page * PER_PAGE
page_indices = filtered[page_start: page_start + PER_PAGE]

render_page(page_indices, set())

st.markdown("---")
col_prev, col_info, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("← Previous", disabled=st.session_state.page == 0):
        st.session_state.page -= 1
        st.rerun()
with col_info:
    st.markdown(
        f"<div style='text-align:center;font-family:DM Mono,monospace;font-size:0.8rem;color:#999;padding-top:0.5rem'>"
        f"Page {st.session_state.page + 1} of {total_pages} &nbsp;·&nbsp; "
        f"Q {page_start + 1}–{min(page_start + PER_PAGE, len(filtered))} of {len(filtered)}</div>",
        unsafe_allow_html=True
    )
with col_next:
    if st.button("Next →", disabled=st.session_state.page >= total_pages - 1):
        st.session_state.page += 1
        st.rerun()
