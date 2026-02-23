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
    multi = len(mc)
    return mc, em, multi


token = st.secrets["HF_TOKEN"]
dataset = load_hle(token)
mc_indices, em_indices, multi = get_question_indices(dataset)

st.set_page_config(page_title="Humanity's Last Exam", page_icon="🧠", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #0a0a0f; color: #e8e6e0; }
h1, h2, h3 { font-family: 'Playfair Display', serif; }
.stApp { background-color: #0a0a0f; }
.hle-header { text-align: center; padding: 2.5rem 0 1.5rem; border-bottom: 1px solid #2a2a3a; margin-bottom: 2rem; }
.hle-header h1 { font-size: 3rem; font-weight: 900; letter-spacing: -1px; color: #f5f0e8; margin: 0; }
.hle-header .subtitle { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #666; letter-spacing: 3px; text-transform: uppercase; margin-top: 0.5rem; }
section[data-testid="stSidebar"] { background: #0d0d18 !important; border-right: 1px solid #2a2a3a; }
.stButton > button { background: #1e1e2e !important; color: #c8a96e !important; border: 1px solid #c8a96e !important; border-radius: 8px !important; font-family: 'DM Mono', monospace !important; font-size: 0.8rem !important; letter-spacing: 1px !important; }
.stButton > button:hover { background: #c8a96e !important; color: #0a0a0f !important; }
.stSelectbox label, .stRadio label, .stTextInput label { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; color: #888 !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
div[data-testid="stMetric"] { background: #13131f; border: 1px solid #2a2a3a; border-radius: 10px; padding: 1rem; }
div[data-testid="stMetric"] label { color: #888 !important; font-family: 'DM Mono', monospace !important; font-size: 0.7rem !important; }
div[data-testid="stMetric"] div { color: #c8a96e !important; font-family: 'Playfair Display', serif !important; }
hr { border-color: #2a2a3a !important; }
.score-box { background: #13131f; border: 1px solid #2a2a3a; border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 2rem; }
.score-num { font-family: 'Playfair Display', serif; font-size: 2.5rem; color: #c8a96e; }
.score-label { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: #666; letter-spacing: 2px; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hle-header">
    <h1>Humanity's Last Exam</h1>
    <div class="subtitle">2,500 questions · expert-vetted · frontier benchmark</div>
</div>
""", unsafe_allow_html=True)

# ── Mode selection ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📚 Mode")
    mode = st.radio("", ["Browse", "Multiple Choice Quiz", "Exact Match Quiz"], label_visibility="collapsed")

    if mode == "Browse":
        answer_types = ["All", "multipleChoice", "exactMatch"]
        type_filter = st.selectbox("Answer Type", answer_types)
        show_answers = st.toggle("Show Answers", value=False)
        st.markdown("---")
        if st.button("🎲 Random Page"):
            st.session_state.browse_page = random.randint(0, len(dataset) // 10)
            st.rerun()

    elif mode == "Multiple Choice Quiz":
        st.markdown("---")
        st.markdown("10 random multiple choice questions")
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
        st.markdown("10 random short answer questions")
        if st.button("🎲 New Quiz"):
            st.session_state.em_questions = random.sample(em_indices, 10)
            st.session_state.em_answers = {}
            st.session_state.em_submitted = False
            st.rerun()
        if st.button("🔄 Reset"):
            for k in ["em_questions", "em_answers", "em_submitted"]:
                st.session_state.pop(k, None)
            st.rerun()


def render_cards(page_indices, show_answers=False):
    cards_html = """
    <html><head>
    <script>window.MathJax = {tex: {inlineMath: [['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}};</script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
    body { background:#0a0a0f; color:#e8e6e0; font-family:'DM Sans',sans-serif; margin:0; padding:4px; }
    .q-card { background:#13131f; border:1px solid #2a2a3a; border-radius:12px; padding:1.5rem; margin-bottom:1.25rem; }
    .q-number { font-family:'DM Mono',monospace; font-size:0.7rem; color:#c8a96e; letter-spacing:2px; text-transform:uppercase; margin-bottom:0.5rem; }
    .q-subject { display:inline-block; font-family:'DM Mono',monospace; font-size:0.65rem; color:#888; background:#1e1e2e; padding:2px 8px; border-radius:20px; margin-bottom:0.75rem; }
    .q-type-badge { font-family:'DM Mono',monospace; font-size:0.65rem; padding:3px 8px; border-radius:4px; background:#1a2a1a; color:#6aaa6a; border:1px solid #2a4a2a; margin-bottom:0.75rem; display:inline-block; margin-left:6px; }
    .q-text { font-size:1rem; line-height:1.7; color:#ddd8cc; margin-bottom:1rem; }
    .answer-box { background:#0d1a0d; border:1px solid #2a4a2a; border-radius:8px; padding:0.75rem 1rem; font-family:'DM Mono',monospace; font-size:0.9rem; color:#7acc7a; margin-top:0.75rem; }
    .answer-label { font-size:0.65rem; color:#4a7a4a; letter-spacing:2px; text-transform:uppercase; margin-bottom:0.3rem; }
    .choices { margin:0.75rem 0; font-size:0.9rem; color:#bbb; }
    .choice { padding:3px 0; }
    </style></head><body>
    """
    for orig_i in page_indices:
        ex = dataset[orig_i]
        subject = ex.get("subject") or "Unknown"
        q_text = ex.get("question", "")
        answer = ex.get("answer", "")
        answer_type = ex.get("answer_type") or "unknown"
        choices = ex.get("answer_choices") or []

        answer_section = ""
        if show_answers:
            answer_section = f'<div class="answer-box"><div class="answer-label">Answer</div>{answer}</div>'

        choices_html = ""
        if answer_type == "multipleChoice" and choices:
            choices_html = '<div class="choices">'
            for c in choices:
                choices_html += f'<div class="choice">▸ {c}</div>'
            choices_html += "</div>"

        cards_html += f"""
        <div class="q-card">
            <div class="q-number">Question #{orig_i + 1}</div>
            <span class="q-subject">{subject}</span><span class="q-type-badge">{answer_type}</span>
            <div class="q-text">{q_text}</div>
            {choices_html}{answer_section}
        </div>"""

    cards_html += "</body></html>"
    components.html(cards_html, height=len(page_indices) * 320, scrolling=True)


# ── Browse mode ───────────────────────────────────────────────────────────────
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

    if filtered_indices:
        render_cards(page_indices, show_answers=show_answers)

        st.markdown("---")
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("← Previous", disabled=st.session_state.browse_page == 0):
                st.session_state.browse_page -= 1
                st.rerun()
        with col_info:
            st.markdown(
                f"<div style='text-align:center;font-family:DM Mono,monospace;font-size:0.8rem;color:#888;padding-top:0.5rem'>"
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
        st.info("Click **🎲 New Quiz** in the sidebar to start a 10-question multiple choice quiz.")
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
                <div>
                    <div class="score-num">{score}/10</div>
                    <div class="score-label">Final Score</div>
                </div>
                <div style="font-family:'DM Sans',sans-serif; color:#888; font-size:0.95rem;">
                    {"🏆 Perfect score! Truly remarkable." if score == 10
                     else "🎉 Excellent!" if score >= 8
                     else "👍 Good effort!" if score >= 5
                     else "📚 Keep studying!"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        for idx, orig_i in enumerate(q_indices):
            ex = dataset[orig_i]
            q_text = ex.get("question", "")
            answer = ex.get("answer", "")
            choices = ex.get("answer_choices") or []
            subject = ex.get("subject") or "Unknown"

            user_answer = st.session_state.mc_answers.get(idx)

            with st.container():
                st.markdown(f"""
                <div style="background:#13131f;border:1px solid #2a2a3a;border-radius:12px;padding:1.5rem;margin-bottom:0.5rem;">
                    <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#c8a96e;letter-spacing:2px;text-transform:uppercase;margin-bottom:0.5rem;">Question {idx + 1} of 10</div>
                    <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#888;background:#1e1e2e;padding:2px 8px;border-radius:20px;display:inline-block;margin-bottom:0.75rem;">{subject}</div>
                </div>
                """, unsafe_allow_html=True)

                # Render question text with MathJax
                q_html = f"""<html><head>
                <script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}}}};</script>
                <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
                <style>body{{background:#13131f;color:#ddd8cc;font-family:'DM Sans',sans-serif;font-size:1rem;line-height:1.7;margin:0;padding:0.5rem 1.5rem;}}</style>
                </head><body>{q_text}</body></html>"""
                components.html(q_html, height=120, scrolling=False)

                if not submitted:
                    selected = st.radio(
                        f"q_{idx}",
                        options=choices,
                        key=f"mc_radio_{idx}",
                        label_visibility="collapsed"
                    )
                    st.session_state.mc_answers[idx] = selected
                else:
                    for c in choices:
                        if c == answer and c == user_answer:
                            st.markdown(f"✅ **{c}** ← your answer (correct!)")
                        elif c == answer:
                            st.markdown(f"✅ **{c}** ← correct answer")
                        elif c == user_answer:
                            st.markdown(f"❌ ~~{c}~~ ← your answer")
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
        st.info("Click **🎲 New Quiz** in the sidebar to start a 10-question short answer quiz.")
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
                <div>
                    <div class="score-num">{score}/10</div>
                    <div class="score-label">Final Score</div>
                </div>
                <div style="font-family:'DM Sans',sans-serif; color:#888; font-size:0.95rem;">
                    {"🏆 Perfect score! Extraordinary." if score == 10
                     else "🎉 Excellent!" if score >= 8
                     else "👍 Good effort!" if score >= 5
                     else "📚 These are PhD-level questions — keep at it!"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        for idx, orig_i in enumerate(q_indices):
            ex = dataset[orig_i]
            q_text = ex.get("question", "")
            answer = ex.get("answer", "")
            subject = ex.get("subject") or "Unknown"
            user_answer = st.session_state.em_answers.get(idx, "")

            st.markdown(f"""
            <div style="background:#13131f;border:1px solid #2a2a3a;border-radius:12px;padding:1.5rem;margin-bottom:0.5rem;">
                <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#c8a96e;letter-spacing:2px;text-transform:uppercase;margin-bottom:0.5rem;">Question {idx + 1} of 10</div>
                <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#888;background:#1e1e2e;padding:2px 8px;border-radius:20px;display:inline-block;margin-bottom:0.75rem;">{subject}</div>
            </div>
            """, unsafe_allow_html=True)

            q_html = f"""<html><head>
            <script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}}}};</script>
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
            <style>body{{background:#13131f;color:#ddd8cc;font-family:'DM Sans',sans-serif;font-size:1rem;line-height:1.7;margin:0;padding:0.5rem 1.5rem;}}</style>
            </head><body>{q_text}</body></html>"""
            components.html(q_html, height=120, scrolling=False)

            if not submitted:
                val = st.text_input(
                    f"Your answer",
                    key=f"em_input_{idx}",
                    placeholder="Type your answer here...",
                    label_visibility="collapsed"
                )
                st.session_state.em_answers[idx] = val
            else:
                is_correct = user_answer.strip().lower() == answer.strip().lower()
                if is_correct:
                    st.markdown(f"✅ **Correct!** Answer: `{answer}`")
                else:
                    st.markdown(f"❌ Your answer: `{user_answer or '(blank)'}` — Correct: `{answer}`")

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
