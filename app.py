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


def split_choices(raw):
    """Split 'A. foo B. bar C. baz' into [('A','foo'),('B','bar'),('C','baz')]."""
    first = re.match(r'^([A-Z])\. ', raw)
    if not first:
        return []
    results = []
    current_label = first.group(1)
    current_start = 3  # skip "A. "
    while True:
        next_label = chr(ord(current_label) + 1)
        m = re.search(' ' + next_label + r'\. ', raw[current_start:])
        if m:
            results.append((current_label, raw[current_start:current_start + m.start()].strip()))
            current_label = next_label
            current_start = current_start + m.start() + len(next_label) + 3
        else:
            results.append((current_label, raw[current_start:].strip()))
            break
    return results


def parse_question(ex):
    """Returns (body_html, choices, answer, answer_type, subject, image_html)."""
    q = ex.get("question", "")
    m = re.search(r'\s*Answer Choices:\s*', q, re.IGNORECASE)
    body = q[:m.start()].strip() if m else q.strip()
    choices_raw = q[m.end():].strip() if m else ""

    # Format triple-backtick code blocks
    body = re.sub(
        r'```(.*?)```',
        lambda x: '<pre style="background:#f4f0e8;border:1px solid #e0dbd0;border-radius:6px;'
                  'padding:0.75rem;font-size:0.82rem;overflow-x:auto;white-space:pre-wrap;'
                  'font-family:monospace;margin:0.5rem 0;">' + x.group(1) + '</pre>',
        body, flags=re.DOTALL
    )

    choices = split_choices(choices_raw) if choices_raw else []

    img = ex.get("image", "")
    if img and not img.startswith("data:"):
        img = "data:image/jpeg;base64," + img
    image_html = f'<img src="{img}" style="max-width:100%;border-radius:8px;border:1px solid #e0dbd0;margin-bottom:1rem;display:block;">' if img else ""

    return (
        body,
        choices,
        ex.get("answer", ""),
        ex.get("answer_type") or "unknown",
        ex.get("subject") or "Unknown",
        image_html,
    )


def render_question(ex, orig_i):
    body, choices, answer, answer_type, subject, image_html = parse_question(ex)

    # Build each choice as its own table row — tables always stack vertically
    rows = ""
    for label, text in choices:
        rows += (
            '<tr>'
            '<td style="padding:8px 10px;vertical-align:top;white-space:nowrap;">'
            f'<b style="font-family:monospace;color:#8a6a2a;">{label}.</b>'
            '</td>'
            f'<td style="padding:8px 14px 8px 4px;line-height:1.5;color:#333;width:100%;">{text}</td>'
            '</tr>'
        )

    choices_html = ""
    if rows:
        choices_html = (
            '<table style="width:100%;border-collapse:separate;border-spacing:0 5px;margin-bottom:1rem;">'
            + rows
            + '</table>'
        )

    answer_safe = answer.replace("<", "&lt;").replace(">", "&gt;")

    html = f"""<!DOCTYPE html>
<html>
<head>
<script>
window.MathJax = {{tex: {{inlineMath: [['$','$'],['\\\\(','\\\\)']], displayMath: [['$$','$$'],['\\\\[','\\\\]']]}}}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #f7f5f0; font-family: 'DM Sans', sans-serif; padding: 4px; }}
  .card {{ background: #fff; border: 1px solid #e0dbd0; border-radius: 12px; padding: 1.25rem 1.5rem; }}
  .meta {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 0.75rem; }}
  .qnum {{ font-family: 'DM Mono', monospace; font-size: 0.65rem; color: #8a6a2a; letter-spacing: 2px; text-transform: uppercase; }}
  .tag {{ font-family: 'DM Mono', monospace; font-size: 0.65rem; padding: 2px 10px; border-radius: 20px; }}
  .tag-subj {{ background: #f0ece4; color: #999; }}
  .tag-type {{ background: #f0f7f0; color: #4a8a4a; border: 1px solid #c0dcc0; border-radius: 4px; padding: 2px 8px; }}
  .body {{ font-size: 1rem; line-height: 1.75; color: #2a2a2a; margin-bottom: 1rem; }}
  .choice-row td {{ background: #faf8f4; border: 1px solid #e8e2d8; }}
  .choice-row td:first-child {{ border-radius: 8px 0 0 8px; border-right: none; }}
  .choice-row td:last-child {{ border-radius: 0 8px 8px 0; }}
  .spoiler {{ display: inline-flex; align-items: center; gap: 8px; cursor: pointer; padding: 7px 14px; background: #f7f5f0; border: 1px solid #e0dbd0; border-radius: 8px; user-select: none; margin-top: 0.25rem; }}
  .spoiler:hover {{ background: #eeeae2; }}
  .lbl {{ font-family: 'DM Mono', monospace; font-size: 0.72rem; color: #8a6a2a; letter-spacing: 1px; }}
  .ans {{ font-family: 'DM Mono', monospace; font-size: 0.9rem; color: #2a6a2a; filter: blur(5px); transition: filter 0.3s; }}
  .spoiler.open .ans {{ filter: blur(0); }}
  .spoiler.open .lbl {{ color: #4a8a4a; }}
</style>
</head>
<body>
<div class="card">
  <div class="meta">
    <span class="qnum">Question #{orig_i + 1}</span>
    <span class="tag tag-subj">{subject}</span>
    <span class="tag tag-type">{answer_type}</span>
  </div>
  {image_html}
  <div class="body">{body}</div>
  {choices_html}
  <div class="spoiler" onclick="this.classList.toggle('open')">
    <span class="lbl">👁 Reveal Answer</span>
    <span class="ans">{answer_safe}</span>
  </div>
</div>
</body>
</html>"""

    body_chars = len(re.sub(r'<[^>]+>', '', body))
    height = 200 + min(body_chars // 4, 1000) + len(choices) * 46
    components.html(html, height=height, scrolling=False)


# ── Setup ─────────────────────────────────────────────────────────────────────
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
.stButton > button { background: #fff !important; color: #8a6a2a !important; border: 1px solid #c8a96e !important; border-radius: 8px !important; font-family: 'DM Mono', monospace !important; font-size: 0.8rem !important; }
.stButton > button:hover { background: #c8a96e !important; color: #fff !important; }
.stSelectbox label { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; color: #666 !important; text-transform: uppercase !important; }
div[data-testid="stMetric"] { background: #fff; border: 1px solid #e0dbd0; border-radius: 10px; padding: 1rem; }
div[data-testid="stMetric"] label { color: #999 !important; font-family: 'DM Mono', monospace !important; font-size: 0.7rem !important; }
div[data-testid="stMetric"] div { color: #8a6a2a !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:2.5rem 0 1.5rem;border-bottom:2px solid #e0dbd0;margin-bottom:2rem;">
  <h1 style="font-family:'Playfair Display',serif;font-size:3rem;font-weight:900;color:#1a1a1a;margin:0;">Humanity's Last Exam</h1>
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

filtered = {"All": all_indices, "multipleChoice": mc_indices, "exactMatch": em_indices}[type_filter]

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Questions", f"{len(dataset):,}")
with col2:
    st.metric("Multiple Choice", f"{len(mc_indices):,}")

st.markdown("<br>", unsafe_allow_html=True)

if "sample" not in st.session_state or st.session_state.get("sample_type") != type_filter:
    st.session_state.sample = random.sample(filtered, min(10, len(filtered)))
    st.session_state.sample_type = type_filter

for orig_i in st.session_state.sample:
    render_question(dataset[orig_i], orig_i)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

st.markdown("---")
if st.button("🎲 New Sample", use_container_width=True):
    st.session_state.pop("sample", None)
    st.rerun()
