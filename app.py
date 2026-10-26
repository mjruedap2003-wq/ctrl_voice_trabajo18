import os
import time
import json
import platform
import streamlit as st
import paho.mqtt.client as paho
from PIL import Image
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# 1. Configuración de página
st.set_page_config(
    page_title="CyberVoice Control | Wokwi Studio 🎙️",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilos Cyberpunk / Neón (CSS)
st.markdown("""
    <style>
    /* Fondo oscuro cibernético */
    .stApp {
        background-color: #0A0E17 !important;
        color: #E2E8F0 !important;
    }
    #MainMenu, footer, header {visibility: hidden;}

    /* Título principal */
    .neon-title {
        font-size: 2.3rem;
        font-weight: 900;
        text-align: center;
        color: #00F0FF;
        text-shadow: 0 0 10px #00F0FF, 0 0 20px #00F0FF;
        margin-bottom: 0.5rem;
    }

    /* Subtítulos en azul neón */
    .cyan-sub-title {
        color: #00F0FF !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        text-shadow: 0 0 8px rgba(0, 240, 255, 0.6) !important;
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
    }

    /* FORZAR BARRA LATERAL OSCURA Y NEÓN */
    section[data-testid="stSidebar"] {
        background-color: #121722 !important;
        border-right: 2px solid #00F0FF !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #00F0FF !important;
        font-weight: bold !important;
        text-shadow: 0 0 5px rgba(0, 240, 255, 0.5) !important;
    }

    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background-color: #1A2232 !important;
        border: 1px solid #00F0FF !important;
        border-radius: 8px !important;
        padding: 10px !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #90CDF4 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #00FF66 !important;
        font-weight: bold !important;
    }

    /* Estado de Lámpara Neón */
    .lamp-on {
        background-color: #122820;
        border: 2px solid #00FF66;
        color: #00FF66;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 800;
        box-shadow: 0 0 20px rgba(0, 255, 102, 0.5);
    }

    .lamp-off {
        background-color: #201218;
        border: 2px solid #FF007F;
        color: #FF007F;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 800;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.3);
    }

    /* Indicador del Servomotor */
    .servo-box {
        background-color: #1A2232;
        border: 2px solid #00F0FF;
        color: #00F0FF;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 800;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.3);
    }

    /* Tarjeta contenedora de información */
    .info-card {
        background: #181E2A;
        border: 1px solid #00F0FF;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }

    /* Botones de Streamlit */
    div.stButton > button {
        width: 100%;
        background: transparent !important;
        color: #00FF66 !important;
        border: 2px solid #00FF66 !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.2) !important;
    }

    div.stButton > button:hover {
        background-color: #00FF66 !important;
        color: #0A0E17 !important;
        box-shadow: 0 0 20px rgba(0, 255, 102, 0.8) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Inicialización del estado de sesión
if "lamp_state" not in st.session_state:
    st.session_state.lamp_state = "OFF"
if "door_state" not in st.session_state:
    st.session_state.door_state = "Cerrada (90°)"
if "voice_history" not in st.session_state:
    st.session_state.voice_history = []
if "commands_count" not in st.session_state:
    st.session_state.commands_count = 0

# Configuración MQTT
broker = "broker.mqttdashboard.com"
port = 1883

def send_voice_mqtt(text_command):
    """Envia el comando de voz al broker MQTT en formato JSON {"Act1": text}"""
    try:
        client1 = paho.Client("VozReceptor")
        client1.connect(broker, port)
        message = json.dumps({"Act1": text_command})
        client1.publish("voice_ctrl", message)
        client1.disconnect()
        return True
    except Exception as e:
        st.error(f"❌ Error al transmitir por MQTT: {e}")
        return False

# --- BARRA LATERAL (ESTADO Y HISTORIAL) ---
with st.sidebar:
    st.markdown('<div class="cyan-sub-title">⚙️ Estado del Sistema</div>', unsafe_allow_html=True)
    st.write(f"**Python:** `v{platform.python_version()}`")
    st.write(f"**Broker MQTT:** `{broker}:{port}`")
    st.write("**Tópico:** `voice_ctrl`")

    st.markdown("---")
    st.markdown('<div class="cyan-sub-title">📊 Registros de Voz</div>', unsafe_allow_html=True)
    st.metric("Comandos Procesados", f"{st.session_state.commands_count}")
    st.metric("Estado Lámpara", st.session_state.lamp_state)
    st.metric("Puerta / Servo", st.session_state.door_state)

    st.markdown("---")
    if st.button("🗑️ Limpiar Historial"):
        st.session_state.voice_history = []
        st.session_state.commands_count = 0
        st.rerun()

# --- ENCABEZADO PRINCIPAL ---
st.markdown('<h1 class="neon-title">🎙️ CYBERVOICE: CONTROL MULTIMODAL ⚡</h1>', unsafe_allow_html=True)

col_top1, col_top2 = st.columns([1, 3])

with col_top1:
    try:
        img_voice = Image.open('voice_ctrl.jpg')
        st.image(img_voice, width=180)
    except Exception:
        pass

with col_top2:
    st.markdown("""
        <div class="info-card">
            <p style="margin:0;">
                🗣️ <strong>Comandos soportados en Wokwi:</strong><br>
                - <code>"enciende las luces"</code> ➔ Encender LED<br>
                - <code>"apaga las luces"</code> ➔ Apagar LED<br>
                - <code>"abre la puerta"</code> ➔ Mover Servo a 180°<br>
                - <code>"Cierra la puerta"</code> ➔ Mover Servo a 90°
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- SECCIÓN 1: RECONOCIMIENTO DE VOZ ---
st.markdown('<div class="cyan-sub-title">🗣️ Captura de Comando por Voz</div>', unsafe_allow_html=True)

stt_button = Button(label="🎙️ TOCAR PARA HABLAR 🎙️", width=300)
stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "es-ES";

    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
"""))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=80,
    debounce_time=0
)

# Procesar resultado de voz
if result and "GET_TEXT" in result:
    raw_text = result.get("GET_TEXT").strip()
    text_lower = raw_text.lower()

    # Transmitir por MQTT
    send_voice_mqtt(raw_text)

    # Evaluar comandos específicos para actualizar interfaz local
    if "enciende" in text_lower or "prender" in text_lower:
        st.session_state.lamp_state = "ON"
    elif "apaga" in text_lower:
        st.session_state.lamp_state = "OFF"

    if "abre" in text_lower:
        st.session_state.door_state = "Abierta (180°)"
    elif "cierra" in text_lower:
        st.session_state.door_state = "Cerrada (90°)"

    timestamp = time.strftime("%H:%M:%S")
    st.session_state.commands_count += 1
    st.session_state.voice_history.insert(0, f"[{timestamp}] 🗣️ \"{raw_text}\"")

# --- SECCIÓN 2: INDICADORES EN TIEMPO REAL ---
st.markdown("---")
st.markdown('<div class="cyan-sub-title">💡 Estado Actual de los Actuadores en Wokwi</div>', unsafe_allow_html=True)

col_ind1, col_ind2 = st.columns(2)

with col_ind1:
    st.markdown("**Luces (Pin 2):**")
    if st.session_state.lamp_state == "ON":
        st.markdown('<div class="lamp-on">💡 LUCES ENCENDIDAS (HIGH)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="lamp-off">🔴 LUCES APAGADAS (LOW)</div>', unsafe_allow_html=True)

with col_ind2:
    st.markdown("**Puerta / Servomotor (Pin 13):**")
    st.markdown(
        f'<div class="servo-box">🚪 {st.session_state.door_state}</div>', 
        unsafe_allow_html=True
    )

# --- SECCIÓN 3: HISTORIAL DE COMANDOS ENVIADOS ---
st.markdown("---")
st.markdown('<div class="cyan-sub-title">📜 Historial de Transmisiones MQTT</div>', unsafe_allow_html=True)

if st.session_state.voice_history:
    for cmd in st.session_state.voice_history[:8]:
        st.markdown(f"- `{cmd}`")
else:
    st.info("💡 Toca el botón de hablar y di: 'enciende las luces', 'apaga las luces', 'abre la puerta' o 'Cierra la puerta'.")
