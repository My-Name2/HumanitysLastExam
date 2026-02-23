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


def get_image_html(ex):
    img_data = ex.get("image")
    if img_data:
        if not img_data.startswith("data:"):
            img_data = f"data:image/jpeg;base64,{img_data}"
        return f'<div style="margin-bottom:1rem;"><img src="{img_data}" style="max-width:100%;border-radius:8px;border:1px solid #e0dbd0;" /></div>'
    return ""


def parse_choices_and_body(ex):
    """Split question into body text and list of choice strings."""
    q = ex.get("question", "")
    match = re.search(r'\s*Answer Choices:\s*', q, re.IGNORECASE)

    if match:
        body = q[:match.start()].strip()
        choices_raw = q[match.end():].strip()
    else:
        body = q.strip()
        choices_raw = ""

    # Format code blocks in body
    body = re.sub(
        r'```(.*?)```',
        r'<pre style="background:#f4f0e8;border:1px solid #e0dbd0;border-radius:6px;padding:0.75rem;font-size:0.82rem;overflow-x:auto;white-space:pre-wrap;font-family:monospace;">\1</pre>',
        body, flags=re.DOTALL
    )

    if not choices_raw:
        return body, []

    # Find sequential letter labels A. B. C. D. E. F. ...
    candidates = [(m.start(), m.group(1)) for m in re.finditer(r'(?:^|(?<= ))([A-Z])\. ', choices_raw)]

    def is_seq(a, b):
        return ord(b) == ord(a) + 1

    if not candidates:
        return body, [choices_raw]

    positions = [candidates[0]]
    for cand in candidates[1:]:
        if is_seq(positions[-1][1], cand[1]):
            positions.append(cand)

    choices = []
    for i, (pos, label) in enumerate(positions):
        start = pos + 3
        end = positions[i + 1][0] if i + 1 < len(positions) else len(choices_raw)
        text = choices_raw[start:end].strip()
        choices.append(f"{label}. {text}")

    return body, choices


CARD_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
* { box-sizing: border-box; }
body { background:#f7f5f0; margin:0; padding:4px 2px; font-family:'DM Sans',sans-serif; }
.q-card { background:#fff; border:1px solid #e0dbd0; border-radius:12px; padding:1.25rem 1.5rem; }
.q-meta { display:flex; align-items:center; gap:8px; margin-bottom:0.75rem; flex-wrap:wrap; }
.q-number { font-family:'DM Mono',monospace; font-size:0.65rem; color:#8a6a2a; letter-spacing:2px; text-transform:uppercase; }
.q-subject { font-family:'DM Mono',monospace; font-size:0.65rem; color:#999; background:#f0ece4; padding:2px 10px; border-radius:20px; }
.q-type { font-family:'DM Mono',monospace; font-size:0.65rem; color:#4a8a4a; background:#f0f7f0; border:1px solid #c0dcc0; padding:2px 8px; border-radius:4px; }
.q-body { font-size:1rem; line-height:1.75; color:#2a2a2a; margin-bottom:1rem; }
.choices { display:flex; flex-direction:column; gap:6px; margin-bottom:1rem; }
.choice { padding:8px 14px; background:#faf8f4; border:1px solid #e8e2d8; border-radius:8px; font-size:0.95rem; color:#333; line-height:1.5; }
.choice strong { color:#8a6a2a; margin-right:4px; }
.spoiler { display:inline-flex; align-items:center; gap:10px; cursor:pointer; padding:7px 14px; background:#f7f5f0; border:1px solid #e0dbd0; border-radius:8px; user-select:none; }
.spoiler:hover { background:#eeeae2; }
.spoiler-label { font-family:'DM Mono',monospace; font-size:0.72rem; color:#8a6a2a; letter-spacing:1px; white-space:nowrap; }
.spoiler-answer { font-family:'DM Mono',monospace; font-size:0.9rem; color:#2a6a2a; filter:blur(5px); transition:filter 0.3s; }
.spoiler.revealed .spoiler-answer { filter:blur(0); }
.spoiler.revealed .spoiler-label { color:#4a8a4a; }
</style>
"""

MATHJAX = """
<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']],displayMath:[['$$','$$'],['\\[','\\]']]}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
"""

def render_question(ex, orig_i):
    subject = ex.get("subject") or "Unknown"
    answer_type = ex.get("answer_type") or "unknown"
    answer = ex.get("answer", "").replace("<", "&lt;").replace(">", "&gt;")
    image_html = get_image_html(ex)
    body, choices = parse_choices_and_body(ex)

    choices_html = ""
    if choices:
        choices_html = '<div class="choices">'
        for c in choices:
            # Bold just the letter label
            c_html = re.sub(r'^([A-Z])\. ', r'<strong>\1.</strong> ', c)
            choices_html += f'<div class="choice">{c_html}</div>'
        choices_html += '</div>'

    html = f"""<!DOCTYPE html><html><head>
    {MATHJAX}
    {CARD_STYLE}
    </head><body>
    <div class="q-card">
        <div class="q-meta">
            <span class="q-number">Question #{orig_i + 1}</span>
            <span class="q-subject">{subject}</span>
            <span class="q-type">{answer_type}</span>
        </div>
        {image_html}
        <div class="q-body">{body}</div>
        {choices_html}
        <div class="spoiler" onclick="this.classList.toggle('revealed')">
            <span class="spoiler-label">👁 Reveal Answer</span>
            <span class="spoiler-answer">{answer}</span>
        </div>
    </div>
    </body></html>"""

    # Height: base + body length + per choice
    height = 160 + min(len(body) // 5, 400) + len(choices) * 56
    components.html(html, height=height, scrolling=False)


# ── App ───────────────────────────────────────────────────────────────────────
token = st.secrets["HF_TOKEN"]
dataset = load_hle(token)
all_indices, mc_indices, em_indices = get_indices(dataset)

st.set_page_config(page_title="Humanity's Last Exam", page_icon="🧠", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #f7f5f0; color: #1a1a1a; }
.stApp { background-color: #f7f5f0; }
section[data-testid="stSidebar"] { background: #eeeae2 !important; border-right: 1px solid #e0dbd0; }
.stButton > button { background: #fff !important; color: #8a6a2a !important; border: 1px solid #c8a96e !important; border-radius: 8px !important; font-family: 'DM Mono', monospace !important; font-size: 0.8rem !important; letter-spacing: 1px !important; }
.stButton > button:hover { background: #c8a96e !important; color: #fff !important; }
.stSelectbox label { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; color: #666 !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
div[data-testid="stMetric"] { background: #fff; border: 1px solid #e0dbd0; border-radius: 10px; padding: 1rem; }
div[data-testid="stMetric"] label { color: #999 !important; font-family: 'DM Mono', monospace !important; font-size: 0.7rem !important; }
div[data-testid="stMetric"] div { color: #8a6a2a !important; font-family: 'Playfair Display', serif !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:2.5rem 0 1.5rem;border-bottom:2px solid #e0dbd0;margin-bottom:2rem;">
    <h1 style="font-family:'Playfair Display',serif;font-size:3rem;font-weight:900;letter-spacing:-1px;color:#1a1a1a;margin:0;">Humanity's Last Exam</h1>
    <div style="font-family:'DM Mono',monospace;font-size:0.75rem;color:#999;letter-spacing:3px;text-transform:uppercase;margin-top:0.5rem;">2,500 questions · expert-vetted · frontier benchmark</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔍 Filter")
    type_filter = st.selectbox("Question Type", ["All", "multipleChoice", "exactMatch"])
    st.markdown("---")
    if st.button("🎲 New Sample", use_container_width=True):
        st.session_state.pop("sample", None)
        st.rerun()

if type_filter == "All":
    filtered = all_indices
elif type_filter == "multipleChoice":
    filtered = mc_indices
else:
    filtered = em_indices

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Questions", f"{len(dataset):,}")
with col2:
    st.metric("Multiple Choice", f"{len(mc_indices):,}")

st.markdown("<br>", unsafe_allow_html=True)

# Resample if filter changed or no sample yet
if "sample" not in st.session_state or st.session_state.get("sample_type") != type_filter:
    st.session_state.sample = random.sample(filtered, min(10, len(filtered)))
    st.session_state.sample_type = type_filter

for orig_i in st.session_state.sample:
    render_question(dataset[orig_i], orig_i)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

st.markdown("---")
if st.button("🎲 New Sample", use_container_width=True):
    st.session_state.pop("sample", None)
    st.rerun()
