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


def parse_choices_from_raw(raw):
    """Parse choices from a raw string. Tries newline-split first, falls back to inline."""
    if not raw:
        return []

    # Strategy 1: newline-separated "A. foo\nB. bar"
    lines = [l.strip() for l in raw.split('\n') if l.strip()]
    choices = []
    for line in lines:
        m = re.match(r'^([A-Z])\.\s+(.*)', line)
        if m:
            choices.append((m.group(1), m.group(2).strip()))
    if len(choices) >= 2:
        return choices

    # Strategy 2: inline "A. foo B. bar C. baz" — walk sequentially
    raw = re.sub(r'(?:^| )([A-Z])\.([^\s])', r' \1. \2', raw).strip()
    m = re.match(r'^([A-Z])\. ', raw)
    if not m:
        return []
    choices = []
    label = m.group(1)
    pos = 3
    while True:
        nxt = chr(ord(label) + 1)
        nxt_m = re.search(' ' + nxt + r'\. ', raw[pos:])
        if nxt_m:
            choices.append((label, raw[pos:pos + nxt_m.start()].strip()))
            label = nxt
            pos = pos + nxt_m.start() + len(nxt) + 3
        else:
            choices.append((label, raw[pos:].strip()))
            break
    return choices if len(choices) >= 2 else []


def parse_question(ex):
    q = ex.get("question", "")

    # Find "Answer Choices:" divider in question text
    m = re.search(r'\s*Answer Choices:\s*', q, re.IGNORECASE)
    if m:
        body = q[:m.start()].strip()
        choices_raw = q[m.end():].strip()
    else:
        # Try detecting inline choices after sentence-ending punctuation "...? A. foo"
        m2 = re.search(r'(?<=[.?!])\s+(A\.)', q)
        if m2:
            body = q[:m2.start()].strip()
            choices_raw = q[m2.start():].strip()
        else:
            body = q.strip()
            choices_raw = ""

    # Format code blocks in body
    body = re.sub(
        r'```(.*?)```',
        lambda x: (
            '<pre style="background:#f4f0e8;border:1px solid #e0dbd0;border-radius:6px;'
            'padding:0.75rem;font-size:0.82rem;overflow-x:auto;white-space:pre-wrap;'
            'font-family:monospace;margin:0.5rem 0;">' + x.group(1) + '</pre>'
        ),
        body, flags=re.DOTALL
    )
    # Convert bare newlines in body to <br> for display
    body = body.replace('\n', '<br>')

    choices = parse_choices_from_raw(choices_raw)

    img = ex.get("image", "")
    if img and not img.startswith("data:"):
        img = "data:image/jpeg;base64," + img

    return (
        body,
        choices,
        ex.get("answer", ""),
        ex.get("answer_type") or "unknown",
        ex.get("subject") or "Unknown",
        img,
    )


def render_question(ex, orig_i):
    body, choices, answer, atype, subject, img = parse_question(ex)

    img_html = ""
    if img:
        img_html = (
            '<img src="' + img + '" style="max-width:100%;border-radius:8px;'
            'border:1px solid #e0dbd0;margin-bottom:1rem;display:block;">'
        )

    choices_html = ""
    if choices:
        for label, text in choices:
            choices_html += (
                '<div style="display:block;width:100%;padding:9px 14px;margin-bottom:6px;'
                'background:#faf8f4;border:1px solid #e8e2d8;border-radius:8px;'
                'font-size:0.95rem;color:#333;line-height:1.5;">'
                '<span style="font-weight:700;color:#8a6a2a;margin-right:8px;'
                'font-family:monospace;">' + label + '.</span>' + text +
                '</div>'
            )
    elif atype == "multipleChoice":
        choices_html = (
            '<div style="padding:8px 14px;margin-bottom:8px;background:#fff8ec;'
            'border:1px solid #f0d090;border-radius:8px;font-family:monospace;'
            'font-size:0.8rem;color:#8a6a2a;">⚠ Answer choices not available in dataset</div>'
        )

    answer_safe = answer.replace("<", "&lt;").replace(">", "&gt;")
    spoiler = (
        '<div id="sp" onclick="'
        'var a=document.getElementById(\'ans\');'
        'var l=document.getElementById(\'lbl\');'
        'if(a.style.filter===\'blur(0px)\'){'
        'a.style.filter=\'blur(5px)\';l.innerText=\'👁 Reveal Answer\';}'
        'else{a.style.filter=\'blur(0px)\';l.innerText=\'✓ Answer\';}"'
        ' style="display:inline-flex;align-items:center;gap:10px;cursor:pointer;'
        'padding:7px 16px;background:#f7f5f0;border:1px solid #e0dbd0;'
        'border-radius:8px;margin-top:4px;">'
        '<span id="lbl" style="font-family:monospace;font-size:0.72rem;'
        'color:#8a6a2a;letter-spacing:1px;">👁 Reveal Answer</span>'
        '<span id="ans" style="font-family:monospace;font-size:0.9rem;color:#2a6a2a;'
        'filter:blur(5px);transition:filter 0.3s;">' + answer_safe + '</span>'
        '</div>'
    )

    html = (
        '<!DOCTYPE html><html><head>'
        '<script>window.MathJax={tex:{inlineMath:[["$","$"],["\\\\(","\\\\)"]],displayMath:[["$$","$$"],["\\\\[","\\\\]"]]}};</script>'
        '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>'
        '<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">'
        '<style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#f7f5f0;font-family:\'DM Sans\',sans-serif;padding:4px;}</style>'
        '</head><body>'
        '<div style="background:#fff;border:1px solid #e0dbd0;border-radius:12px;padding:1.25rem 1.5rem;">'
        '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:0.75rem;">'
        '<span style="font-family:monospace;font-size:0.65rem;color:#8a6a2a;letter-spacing:2px;text-transform:uppercase;">Question #' + str(orig_i + 1) + '</span>'
        '<span style="font-family:monospace;font-size:0.65rem;color:#999;background:#f0ece4;padding:2px 10px;border-radius:20px;">' + subject + '</span>'
        '<span style="font-family:monospace;font-size:0.65rem;color:#4a8a4a;background:#f0f7f0;border:1px solid #c0dcc0;padding:2px 8px;border-radius:4px;">' + atype + '</span>'
        '</div>'
        + img_html
        + '<div style="font-size:1rem;line-height:1.75;color:#2a2a2a;margin-bottom:1rem;">' + body + '</div>'
        + choices_html
        + spoiler
        + '</div></body></html>'
    )

    body_chars = len(re.sub(r'<[^>]+>', '', body))
    height = 160 + min(body_chars // 5, 800) + len(choices) * 52 + (40 if not choices and atype == "multipleChoice" else 0)
    components.html(html, height=height, scrolling=True)


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
    st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

st.markdown("---")
if st.button("🎲 New Sample", use_container_width=True):
    st.session_state.pop("sample", None)
    st.rerun()
