import re
import random
import streamlit as st
import streamlit.components.v1 as components
from datasets import load_dataset


@st.cache_resource(show_spinner="Loading dataset...")
def load_hle(token):
    return load_dataset("cais/hle", split="test", token=token)


@st.cache_data(show_spinner=False)
def get_question_indices(_dataset):
    mc = [i for i, ex in enumerate(_dataset) if ex.get("answer_type") == "multipleChoice"]
    em = [i for i, ex in enumerate(_dataset) if ex.get("answer_type") == "exactMatch"]
    return mc, em, len(mc)


def parse_choices(ex):
    """Get answer choices — from field first, then extract from question text."""
    choices = ex.get("answer_choices") or []
    if choices:
        return choices

    q = ex.get("question", "")
    match = re.search(r'Answer Choices:\s*(.*?)$', q, re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    raw = match.group(1).strip()
    # Split on A. B. C. D. E. at word boundaries (max 5 options)
    parts = re.split(r'(?<!\w)([A-E])\.\s', raw)
    # parts will be like ['', 'A', 'text...', 'B', 'text...']
    choices = []
    for i in range(1, len(parts) - 1, 2):
        label = parts[i]
        text = parts[i + 1].strip().rstrip()
        choices.append(f"{label}. {text}")
    return choices


def clean_question_text(ex):
    """Remove embedded Answer Choices block from question text."""
    q = ex.get("question", "")
    return re.sub(r'\s*Answer Choices:.*$', '', q, flags=re.IGNORECASE | re.DOTALL).strip()


def make_card_html(ex, orig_i, show_answer=False, label=None):
    subject = ex.get("subject") or "Unknown"
    q_text = clean_question_text(ex)
    answer = ex.get("answer", "")
    answer_type = ex.get("answer_type") or "unknown"
    choices = parse_choices(ex)

    # Format code blocks
    q_text = re.sub(r'```(.*?)```', r'<pre style="background:#f4f0e8;border:1px solid #e0dbd0;border-radius:6px;padding:0.75rem;font-size:0.85rem;overflow-x:auto;white-space:pre-wrap;">\1</pre>', q_text, flags=re.DOTALL)

    display_label = label if label else f"Question #{orig_i + 1}"

    choices_html = ""
    if choices:
        choices_html = '<div style="margin-top:1rem;display:flex;flex-direction:column;gap:6px;">'
        for c in choices:
            choices_html += f'<div style="padding:8px 12px;background:#faf8f4;border:1px solid #e8e2d8;border-radius:8px;font-size:0.95rem;color:#333;">▸ {c}</div>'
        choices_html += '</div>'

    answer_html = ""
    if show_answer:
        answer_html = f'''<div style="margin-top:1rem;background:#f0f7f0;border:1px solid #c0dcc0;border-radius:8px;padding:0.75rem 1rem;">
            <div style="font-family:'DM Mono',monospace;font-size:0.6rem;color:#4a8a4a;letter-spacing:2px;text-transform:uppercase;margin-bottom:0.3rem;">Answer</div>
            <div style="font-family:'DM Mono',monospace;font-size:0.9rem;color:#2a6a2a;">{answer}</div>
        </div>'''

    return f'''
    <div style="background:#fff;border:1px solid #e0dbd0;border-radius:12px;padding:1.5rem;margin-bottom:1.25rem;">
        <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#8a6a2a;letter-spacing:2px;text-transform:uppercase;margin-bottom:0.6rem;">{display_label}</div>
        <div style="margin-bottom:0.6rem;">
            <span style="display:inline-block;font-family:'DM Mono',monospace;font-size:0.65rem;color:#999;background:#f0ece4;padding:2px 10px;border-radius:20px;">{subject}</span>
            <span style="display:inline-block;font-family:'DM Mono',monospace;font-size:0.65rem;color:#4a8a4a;background:#f0f7f0;border:1px solid #c0dcc0;padding:2px 8px;border-radius:4px;margin-left:6px;">{answer_type}</span>
        </div>
        <div style="font-size:1rem;line-height:1.75;color:#2a2a2a;margin-top:0.75rem;">{q_text}</div>
        {choices_html}
        {answer_html}
    </div>'''


def render_cards(page_indices, show_answers=False):
    body = ""
    for orig_i in page_indices:
        ex = dataset[orig_i]
        body += make_card_html(ex, orig_i, show_answer=show_answers)

    html = f"""<html><head>
    <script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}}}};</script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
    body {{ background:#f7f5f0; margin:0; padding:4px; font-family:'DM Sans',sans-serif; }}
    </style>
    </head><body>{body}</body></html>"""
    components.html(html, height=len(page_indices) * 360, scrolling=True)


def render_single_q(ex, orig_i, label=None):
    body = make_card_html(ex, orig_i, show_answer=False, label=label)
    html = f"""<html><head>
    <script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}}}};</script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
    body {{ background:#f7f5f0; margin:0; padding:4px; font-family:'DM Sans',sans-serif; }}
    </style>
    </head><body>{body}</body></html>"""
    components.html(html, height=280, scrolling=False)


# ── Load ──────────────────────────────────────────────────────────────────────
token = st.secrets["HF_TOKEN"]
dataset = load_hle(token)
mc_indices, em_indices, multi = get_question_indices(dataset)

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
.stSelectbox label, .stRadio label, .stTextInput label { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; color: #666 !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
div[data-testid="stMetric"] { background: #fff; border: 1px solid #e0dbd0; border-radius: 10px; padding: 1rem; }
div[data-testid="stMetric"] label { color: #999 !important; font-family: 'DM Mono', monospace !important; font-size: 0.7rem !important; }
div[data-testid="stMetric"] div { color: #8a6a2a !important; font-family: 'Playfair Display', serif !important; }
hr { border-color: #e0dbd0 !important; }
.score-box { background: #fff; border: 1px solid #e0dbd0; border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 2rem; }
.score-num { font-family: 'Playfair Display', serif; font-size: 2.5rem; color: #8a6a2a; }
.score-label { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: #999; letter-spacing: 2px; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hle-header">
    <h1>Humanity's Last Exam</h1>
    <div class="subtitle">2,500 questions · expert-vetted · frontier benchmark</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📚 Mode")
    mode = st.radio("", ["Browse", "Multiple Choice Quiz", "Exact Match Quiz"], label_visibility="collapsed")

    if mode == "Browse":
        type_filter = st.selectbox("Answer Type", ["All", "multipleChoice", "exactMatch"])
        show_answers = st.toggle("Show Answers", value=False)
        st.markdown("---")
        if st.button("🎲 Random Page"):
            st.session_state.browse_page = random.randint(0, len(dataset) // 10)
            st.rerun()

    elif mode == "Multiple Choice Quiz":
        st.markdown("---")
        st.caption("10 random multiple choice questions")
        if st.button("🎲 New Quiz"):
            st.session_state.mc_questions = random.sample(mc_indices, 10)
            st.session_state.mc_answers = {}
            st.session_state.mc_submitted = False
            st.rerun()
        if st.button("🔄 Reset"):
            for k in ["mc_questions", "mc_answers", "mc_submitted"]:
                st.session_state.pop(k, None)
            st.rerun()

    elif mode == "Exact Match Quiz":
        st.markdown("---")
        st.caption("10 random short answer questions")
        if st.button("🎲 New Quiz"):
            st.session_state.em_questions = random.sample(em_indices, 10)
            st.session_state.em_answers = {}
            st.session_state.em_submitted = False
            st.rerun()
        if st.button("🔄 Reset"):
            for k in ["em_questions", "em_answers", "em_submitted"]:
                st.session_state.pop(k, None)
            st.rerun()

# ── Browse ────────────────────────────────────────────────────────────────────
if mode == "Browse":
    filtered_indices = [
        i for i, ex in enumerate(dataset)
        if (type_filter == "All" or (ex.get("answer_type") or "Unknown") == type_filter)
    ]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions", f"{len(dataset):,}")
    with col2:
        st.metric("Filtered", f"{len(filtered_indices):,}")
    with col3:
        st.metric("Multiple Choice", f"{multi:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    PER_PAGE = 10
    if "browse_page" not in st.session_state:
        st.session_state.browse_page = 0

    total_pages = max(1, (len(filtered_indices) - 1) // PER_PAGE + 1)
    st.session_state.browse_page = min(st.session_state.browse_page, total_pages - 1)
    page_start = st.session_state.browse_page * PER_PAGE
    page_indices = filtered_indices[page_start: page_start + PER_PAGE]

    render_cards(page_indices, show_answers=show_answers)

    st.markdown("---")
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("← Previous", disabled=st.session_state.browse_page == 0):
            st.session_state.browse_page -= 1
            st.rerun()
    with col_info:
        st.markdown(
            f"<div style='text-align:center;font-family:DM Mono,monospace;font-size:0.8rem;color:#999;padding-top:0.5rem'>"
            f"Page {st.session_state.browse_page + 1} of {total_pages} &nbsp;·&nbsp; "
            f"Q {page_start + 1}–{min(page_start + PER_PAGE, len(filtered_indices))} of {len(filtered_indices)}</div>",
            unsafe_allow_html=True
        )
    with col_next:
        if st.button("Next →", disabled=st.session_state.browse_page >= total_pages - 1):
            st.session_state.browse_page += 1
            st.rerun()

# ── Multiple Choice Quiz ──────────────────────────────────────────────────────
elif mode == "Multiple Choice Quiz":
    if "mc_questions" not in st.session_state:
        st.info("Click **🎲 New Quiz** in the sidebar to start.")
    else:
        q_indices = st.session_state.mc_questions
        submitted = st.session_state.get("mc_submitted", False)

        if submitted:
            score = sum(
                1 for idx, orig_i in enumerate(q_indices)
                if st.session_state.mc_answers.get(idx) == dataset[orig_i]["answer"]
            )
            st.markdown(f"""
            <div class="score-box">
                <div><div class="score-num">{score}/10</div><div class="score-label">Final Score</div></div>
                <div style="font-family:'DM Sans',sans-serif;color:#666;font-size:0.95rem;">
                    {"🏆 Perfect score! Truly remarkable." if score == 10
                     else "🎉 Excellent!" if score >= 8
                     else "👍 Good effort!" if score >= 5
                     else "📚 Keep studying!"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        for idx, orig_i in enumerate(q_indices):
            ex = dataset[orig_i]
            answer = ex.get("answer", "")
            choices = parse_choices(ex)
            user_answer = st.session_state.mc_answers.get(idx)

            render_single_q(ex, orig_i, label=f"Question {idx + 1} of 10")

            if not submitted:
                if choices:
                    selected = st.radio(
                        f"q_{idx}",
                        options=choices,
                        key=f"mc_radio_{idx}",
                        label_visibility="collapsed"
                    )
                    st.session_state.mc_answers[idx] = selected
                else:
                    st.warning("No choices found for this question.")
            else:
                for c in choices:
                    if c == answer and c == user_answer:
                        st.success(f"✅ **{c}** ← your answer (correct!)")
                    elif c == answer:
                        st.success(f"✅ **{c}** ← correct answer")
                    elif c == user_answer:
                        st.error(f"❌ {c} ← your answer")
                    else:
                        st.markdown(f"○ {c}")

            st.markdown("<br>", unsafe_allow_html=True)

        if not submitted:
            if st.button("Submit Quiz", use_container_width=True):
                st.session_state.mc_submitted = True
                st.rerun()
        else:
            if st.button("🎲 New Quiz", use_container_width=True):
                st.session_state.mc_questions = random.sample(mc_indices, 10)
                st.session_state.mc_answers = {}
                st.session_state.mc_submitted = False
                st.rerun()

# ── Exact Match Quiz ──────────────────────────────────────────────────────────
elif mode == "Exact Match Quiz":
    if "em_questions" not in st.session_state:
        st.info("Click **🎲 New Quiz** in the sidebar to start.")
    else:
        q_indices = st.session_state.em_questions
        submitted = st.session_state.get("em_submitted", False)

        if submitted:
            score = sum(
                1 for idx, orig_i in enumerate(q_indices)
                if st.session_state.em_answers.get(idx, "").strip().lower() == dataset[orig_i]["answer"].strip().lower()
            )
            st.markdown(f"""
            <div class="score-box">
                <div><div class="score-num">{score}/10</div><div class="score-label">Final Score</div></div>
                <div style="font-family:'DM Sans',sans-serif;color:#666;font-size:0.95rem;">
                    {"🏆 Perfect score! Extraordinary." if score == 10
                     else "🎉 Excellent!" if score >= 8
                     else "👍 Good effort!" if score >= 5
                     else "📚 These are PhD-level questions — keep at it!"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        for idx, orig_i in enumerate(q_indices):
            ex = dataset[orig_i]
            answer = ex.get("answer", "")
            user_answer = st.session_state.em_answers.get(idx, "")

            render_single_q(ex, orig_i, label=f"Question {idx + 1} of 10")

            if not submitted:
                val = st.text_input(
                    "Your answer",
                    key=f"em_input_{idx}",
                    placeholder="Type your answer here...",
                    label_visibility="collapsed"
                )
                st.session_state.em_answers[idx] = val
            else:
                is_correct = user_answer.strip().lower() == answer.strip().lower()
                if is_correct:
                    st.success(f"✅ Correct! Answer: `{answer}`")
                else:
                    st.error(f"❌ Your answer: `{user_answer or '(blank)'}` — Correct: `{answer}`")

            st.markdown("<br>", unsafe_allow_html=True)

        if not submitted:
            if st.button("Submit Quiz", use_container_width=True):
                st.session_state.em_submitted = True
                st.rerun()
        else:
            if st.button("🎲 New Quiz", use_container_width=True):
                st.session_state.em_questions = random.sample(em_indices, 10)
                st.session_state.em_answers = {}
                st.session_state.em_submitted = False
                st.rerun()
