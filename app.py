import streamlit as st
import anthropic
import json
import time

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🧠 AI Overthinking Manager",
    page_icon="🧠",
    layout="centered",
)

# ─── STYLING ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0a0a0f;
    color: #e8e8e8;
}

/* Hide Streamlit default elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 720px; }

/* Title */
.main-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    color: #fff;
    text-align: center;
    letter-spacing: -1px;
    margin-bottom: 0;
}
.main-title span { color: #ff2d55; }
.subtitle {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #444;
    text-align: center;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.card-red {
    background: rgba(255,45,85,0.08);
    border: 1px solid rgba(255,45,85,0.3);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    text-align: center;
}
.card-green {
    background: rgba(48,209,88,0.08);
    border: 1px solid rgba(48,209,88,0.3);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.card-blue {
    background: rgba(50,173,230,0.08);
    border: 1px solid rgba(50,173,230,0.3);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    text-align: center;
}

/* Labels */
.step-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: #ff2d55;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.diagnosis-text {
    font-family: 'Space Mono', monospace;
    font-size: 1.2rem;
    font-weight: 700;
    color: #fff;
}
.distortion-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 6px;
}
.body-text { color: #aaa; font-size: 0.9rem; line-height: 1.6; }
.prob-number { font-family: 'Space Mono', monospace; font-size: 2rem; font-weight: 700; }
.rational { color: #d0f0c0; font-size: 0.95rem; line-height: 1.6; }
.mantra { font-family: 'Space Mono', monospace; font-size: 1rem; font-weight: 700; color: #32ade6; }
.italic-text { color: #888; font-size: 0.85rem; font-style: italic; }

/* Sticker badge */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres el "AI Overthinking Manager" — un agente con personalidad que ayuda a las personas a salir de espirales de overthinking y catastrofización.

Cuando el usuario comparta un pensamiento ansioso o catastrófico, responde ÚNICAMENTE con JSON válido y nada más. Sin markdown, sin bloques de código, sin explicación previa. Solo el JSON puro.

Estructura exacta:
{
  "distortion": {
    "name": "nombre de la distorsión cognitiva detectada",
    "emoji": "emoji relevante",
    "description": "explicación breve y con humor de qué está pasando"
  },
  "probability": {
    "real": número entre 2 y 40,
    "catastrophe_level": "MÁXIMA CATÁSTROFE" o "ALTA" o "MEDIA" o "BAJA" o "CASI NULA",
    "funny_comparison": "comparación graciosa de la probabilidad real vs la percibida"
  },
  "reframe": {
    "rational_thought": "versión racional del pensamiento",
    "action": "acción concreta y pequeña que puede tomar"
  },
  "confidence_boost": {
    "message": "mensaje empoderador y divertido de 2-3 oraciones",
    "mantra": "mantra corto y memorable, máximo 8 palabras"
  },
  "diagnosis": "nombre dramático y divertido para este episodio (ej: 'Síndrome del Apocalipsis Laboral Inminente')"
}

Sé empático pero con humor. No seas condescendiente. Usa español."""

# ─── HELPERS ─────────────────────────────────────────────────────────────────
CATASTROPHE_COLORS = {
    "MÁXIMA CATÁSTROFE": "#ff2d55",
    "ALTA": "#ff6b35",
    "MEDIA": "#ffd60a",
    "BAJA": "#30d158",
    "CASI NULA": "#32ade6",
}

EXAMPLES = [
    "Creo que mi jefe me odia porque no me contestó el mail en 2 horas",
    "Mi amigo tardó en responder WhatsApp, seguro está enojado conmigo",
    "Me equivoqué en una reunión, todos deben pensar que soy incompetente",
    "No dormí bien, mañana voy a arruinar todo en el trabajo",
]

def call_claude(thought: str) -> dict:
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": thought}],
    )
    text = response.content[0].text.strip()
    # Strip possible markdown fences
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ─── UI ───────────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">OVERTHINKING<span>.</span>MANAGER</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">v1.0 · Análisis cognitivo en tiempo real · Powered by LangChain + Claude</div>', unsafe_allow_html=True)

# API Key input
with st.expander("🔑 Configurar API Key", expanded=not st.session_state.api_key):
    key_input = st.text_input("Anthropic API Key", type="password", value=st.session_state.api_key, placeholder="sk-ant-...")
    if key_input:
        st.session_state.api_key = key_input
        st.success("✅ API Key guardada")

st.divider()

# Input area
st.markdown("##### 📥 ¿Qué estás dramatizando hoy?")

# Example buttons
cols = st.columns(2)
for i, ex in enumerate(EXAMPLES):
    if cols[i % 2].button(f"💭 {ex[:40]}...", key=f"ex_{i}", use_container_width=True):
        st.session_state.prefill = ex

thought = st.text_area(
    "Tu pensamiento catastrófico:",
    value=st.session_state.get("prefill", ""),
    placeholder="Ej: 'Creo que mi jefe me odia porque no respondió mi mail...'",
    height=100,
    label_visibility="collapsed",
)
if "prefill" in st.session_state:
    del st.session_state.prefill

analyze_btn = st.button("⚡ ANALIZAR PENSAMIENTO", type="primary", use_container_width=True, disabled=not thought.strip())

# ─── ANALYSIS ─────────────────────────────────────────────────────────────────
if analyze_btn and thought.strip():
    if not st.session_state.api_key:
        st.error("⚠️ Primero configura tu API Key de Anthropic.")
    else:
        st.divider()
        
        with st.spinner("🧠 Escaneando catástrofe inminente..."):
            try:
                result = call_claude(thought)
                st.session_state.history.insert(0, {"input": thought, "result": result})
            except Exception as e:
                st.error(f"Error al analizar: {e}")
                result = None

        if result:
            # --- Diagnosis banner
            st.markdown(f"""
            <div class="card-red">
                <div class="step-label">🔬 DIAGNÓSTICO OFICIAL</div>
                <div class="diagnosis-text">"{result['diagnosis']}"</div>
            </div>
            """, unsafe_allow_html=True)

            time.sleep(0.1)

            # --- Step 1: Distortion
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <div class="step-label">PASO 1 · CATASTROPHIZING_DETECTOR</div>
                    <div style="display:flex;gap:16px;align-items:flex-start">
                        <div style="font-size:2.5rem;line-height:1">{result['distortion']['emoji']}</div>
                        <div>
                            <div class="distortion-name">{result['distortion']['name']}</div>
                            <div class="body-text">{result['distortion']['description']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # --- Step 2: Probability
            prob = result["probability"]
            color = CATASTROPHE_COLORS.get(prob["catastrophe_level"], "#fff")
            
            st.markdown(f"""
            <div class="card">
                <div class="step-label">PASO 2 · PROBABILITY_ESTIMATOR</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                    <span class="body-text">Probabilidad real del desastre</span>
                    <span class="prob-number" style="color:{color}">{prob['real']}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            progress_val = prob["real"] / 100
            st.progress(progress_val)
            
            st.markdown(f"""
            <div style="margin-top:8px;margin-bottom:16px">
                <span class="badge" style="background:{color}22;color:{color};border:1px solid {color}44">
                    NIVEL: {prob['catastrophe_level']}
                </span>
                <div class="italic-text" style="margin-top:8px">💡 {prob['funny_comparison']}</div>
            </div>
            """, unsafe_allow_html=True)

            # --- Step 3: Reframe
            st.markdown(f"""
            <div class="card">
                <div class="step-label">PASO 3 · RATIONAL_REFRAME_TOOL</div>
                <div style="margin-bottom:14px">
                    <div style="font-size:0.7rem;color:#555;margin-bottom:6px;text-transform:uppercase;letter-spacing:1px">Pensamiento racional:</div>
                    <div class="rational" style="padding:12px;background:rgba(48,209,88,0.08);border-radius:8px;border-left:3px solid #30d158">
                        {result['reframe']['rational_thought']}
                    </div>
                </div>
                <div>
                    <div style="font-size:0.7rem;color:#555;margin-bottom:6px;text-transform:uppercase;letter-spacing:1px">Acción concreta:</div>
                    <div class="body-text">→ {result['reframe']['action']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- Step 4: Confidence boost
            st.markdown(f"""
            <div class="card-blue">
                <div class="step-label">PASO 4 · CONFIDENCE_BOOSTER</div>
                <div class="body-text" style="color:#ccc;margin-bottom:16px;font-size:0.95rem">
                    {result['confidence_boost']['message']}
                </div>
                <div class="mantra">✦ "{result['confidence_boost']['mantra']}"</div>
            </div>
            """, unsafe_allow_html=True)

# ─── HISTORY ──────────────────────────────────────────────────────────────────
if len(st.session_state.history) > 1:
    st.divider()
    st.markdown("##### 📋 Historial de catástrofes")
    for i, item in enumerate(st.session_state.history[1:6]):
        with st.expander(f"💭 {item['input'][:60]}...  —  {item['result']['probability']['real']}% riesgo"):
            r = item["result"]
            st.markdown(f"**Diagnóstico:** {r['diagnosis']}")
            st.markdown(f"**Distorsión:** {r['distortion']['emoji']} {r['distortion']['name']}")
            st.markdown(f"**Mantra:** _{r['confidence_boost']['mantra']}_")

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;margin-top:48px;font-family:'Space Mono',monospace;font-size:0.6rem;color:#333;letter-spacing:1px">
NO SOMOS TERAPEUTAS · SÍ SOMOS ÚTILES · POWERED BY LANGCHAIN + CLAUDE
</div>
""", unsafe_allow_html=True)