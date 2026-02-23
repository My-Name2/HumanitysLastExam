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


def split_choices(raw):
    """Split a choices string like 'A. foo B. bar C. baz' into [('A','foo'),('B','bar'),('C','baz')]."""
    first = re.match(r'^([A-Z])\. ', raw)
    if not first:
        return [('', raw)]
    results = []
    current_label = first.group(1)
    current_start = 3  # skip "A. "
    while True:
        next_label = chr(ord(current_label) + 1)
        m = re.search(r' ' + next_label + r'\. ', raw[current_start:])
        if m:
            results.append((current_label, raw[current_start:current_start + m.start()].strip()))
            current_label = next_label
            current_start = current_start + m.start() + len(next_label) + 3
        else:
            results.append((current_label, raw[current_start:].strip()))
            break
    return results


def parse_choices_and_body(ex):
    q = ex.get("question", "")
    match = re.search(r'\s*Answer Choices:\s*', q, re.IGNORECASE)

    if match:
        body = q[:match.start()].strip()
        choices_raw = q[match.end():].strip()
    else:
        body = q.strip()
        choices_raw = ""

    # Format code blocks
    body = re.sub(
        r'```(.*?)```',
        r'<pre style="background:#f4f0e8;border:1px solid #e0dbd0;border-radius:6px;padding:0.75rem;font-size:0.82rem;overflow-x:auto;white-space:pre-wrap;font-family:monospace;">\1</pre>',
        body, flags=re.DOTALL
    )

    if not choices_raw:
        return body, []

    return body, split_choices(choices_raw)


def render_question(ex, orig_i):
    subject = ex.get("subject") or "Unknown"
    answer_type = ex.get("answer_type") or "unknown"
    answer = ex.get("answer", "").replace("<", "&lt;").replace(">", "&gt;")
    image_html = get_image_html(ex)
    body, choices = parse_choices_and_body(ex)

    # Build choices HTML with fully inline styles — no CSS classes
    choices_html = ""
    if choices:
        choices_html = '<div style="margin:0 0 1rem 0;">'
        for label, text in choices:
            label_html = f'<b style="color:#8a6a2a;margin-right:6px;">{label}.</b>' if label else ''
            choices_html += (
                f'<div style="display:block;padding:8px 14px;background:#faf8f4;border:1px solid #e8e2d8;border-radius:8px;font-size:0.95rem;color:#333;line-height:1.5;margin-bottom:6px;">'
                f'{label_html}{text}</div>'
            )
        choices_html += '</div>'

    html = (
        '<!DOCTYPE html><html><head>'
        '<script>window.MathJax={tex:{inlineMath:[["$","$"],["\\\\(","\\\\)"]],displayMath:[["$$","$$"],["\\\\[","\\\\]"]]}};</script>'
        '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>'
        '<style>'
        'body{background:#f7f5f0;margin:0;padding:4px 2px;font-family:\'DM Sans\',sans-serif;}'
        '@import url("https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap");'
        '.spoiler{display:inline-flex;align-items:center;gap:10px;cursor:pointer;padding:7px 14px;'
        'background:#f7f5f0;border:1px solid #e0dbd0;border-radius:8px;user-select:none;}'
        '.spoiler:hover{background:#eeeae2;}'
        '.spoiler-label{font-family:"DM Mono",monospace;font-size:0.72rem;color:#8a6a2a;letter-spacing:1px;}'
        '.spoiler-answer{font-family:"DM Mono",monospace;font-size:0.9rem;color:#2a6a2a;filter:blur(5px);transition:filter 0.3s;}'
        '.spoiler.revealed .spoiler-answer{filter:blur(0);}'
        '.spoiler.revealed .spoiler-label{color:#4a8a4a;}'
        '</style>'
        '</head><body>'
        '<div style="background:#fff;border:1px solid #e0dbd0;border-radius:12px;padding:1.25rem 1.5rem;">'
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;flex-wrap:wrap;">'
        f'<span style="font-family:\'DM Mono\',monospace;font-size:0.65rem;color:#8a6a2a;letter-spacing:2px;text-transform:uppercase;">Question #{orig_i + 1}</span>'
        f'<span style="font-family:\'DM Mono\',monospace;font-size:0.65rem;color:#999;background:#f0ece4;padding:2px 10px;border-radius:20px;">{subject}</span>'
        f'<span style="font-family:\'DM Mono\',monospace;font-size:0.65rem;color:#4a8a4a;background:#f0f7f0;border:1px solid #c0dcc0;padding:2px 8px;border-radius:4px;">{answer_type}</span>'
        '</div>'
        + image_html
        + f'<div style="font-size:1rem;line-height:1.75;color:#2a2a2a;margin-bottom:1rem;">{body}</div>'
        + choices_html
        + '<div class="spoiler" onclick="this.classList.toggle(\'revealed\')">'
        + '<span class="spoiler-label">👁 Reveal Answer</span>'
        + f'<span class="spoiler-answer">{answer}</span>'
        + '</div>'
        + '</div></body></html>'
    )

    body_chars = len(re.sub(r'<[^>]+>', '', body))
    body_lines = body.count('\n') + 1
    height = 180 + min(body_chars // 4, 1200) + body_lines * 18 + len(choices) * 60
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
