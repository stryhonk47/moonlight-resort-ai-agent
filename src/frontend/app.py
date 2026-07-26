import os
import re
import sys
import streamlit as st

# Añadir el directorio raíz al path para importar backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from src.backend.rag_pipeline import MoonlightRAG

# Configuración de la página en Streamlit (Layout amplio para que luzca la barra lateral)
st.set_page_config(
    page_title="Moonlight Resort - Conserje IA",
    page_icon="🌙",
    layout="wide"
)

# Estilos CSS personalizados para dar un aspecto limpio y corporativo
st.markdown("""
<style>
    .chat-header {
        margin-bottom: 1.5rem;
    }
    .resort-title {
        color: #1E3A8A;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        margin-bottom: 0rem;
    }
    .resort-subtitle {
        color: #4B5563;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 🌟 BARRA LATERAL (SIDEBAR) - INFORMACIÓN Y EJEMPLOS DE PREGUNTAS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🌙 Moonlight Resort")
    st.markdown(
        "Asistente IA para consultar el **catálogo comercial de habitaciones**, tarifas, "
        "políticas de cancelación, horarios de servicio y visualizar las "
        "**fotografías oficiales** del complejo."
    )
    st.markdown("---")
    st.markdown("#### 💡 Ejemplos de preguntas:")
    st.markdown("""
    - **Cotización:** *¿Cuánto cuesta la Master Suite por 2 noches y qué incluye?*
    - **Políticas:** *¿Puedo llevar a mi perro al hotel? ¿Puede entrar a la piscina?*
    - **Catálogo visual:** *¿Puedes mostrarme una foto de la piscina para adultos?*
    - **Cancelaciones:** *¿Qué sucede si cancelo mi reserva con 24 horas de anticipación?*
    - **Horarios:** *¿A qué hora abre el Restaurante Gourmet y cuál es el código de vestimenta?*
    """)
    st.markdown("---")
    
    # Botón para limpiar la conversación y empezar de cero
    if st.button("🗑️ Limpiar historial de chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Historial limpiado! 🌴 Soy el conserje digital de Moonlight Resort. ¿En qué puedo asistirle hoy?"}
        ]
        st.rerun()

# -----------------------------------------------------------------------------
# 🤖 MOTOR RAG Y GESTIÓN DE SESIÓN
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Cargando base de datos del resort y conectando a Cohere...")
def get_rag_engine():
    return MoonlightRAG()

try:
    rag_engine = get_rag_engine()
except Exception as e:
    st.error(f"❌ Error fatal al iniciar el motor IA: {str(e)}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy el conserje digital de Moonlight Resort 🌴. ¿En qué puedo ayudarle hoy? Puedo informarle sobre nuestras habitaciones, realizar cotizaciones, explicarle nuestras normas o mostrarle fotografías de nuestras instalaciones."}
    ]

# -----------------------------------------------------------------------------
# 📸 PARSER VISUAL Y INTERFAZ DE CHAT CENTRAL
# -----------------------------------------------------------------------------
# Encabezado central de la interfaz
st.markdown("<div class='chat-header'><h1 class='resort-title'>🌙 Moonlight Resort</h1><p class='resort-subtitle'>Asistente Virtual y Conserje de Lujo (Powered by RAG & Cohere)</p></div>", unsafe_allow_html=True)

def render_message_with_images(text: str):
    pattern = r"\[ID_IMAGEN:\s*([A-Za-z0-9_]+)\]"
    matches = re.findall(pattern, text)
    clean_text = re.sub(pattern, "", text).strip()
    
    st.markdown(clean_text)
    
    if matches:
        images_dir = os.path.join(BASE_DIR, "data", "images")
        for img_id in matches:
            img_path = None
            for ext in [".jpg", ".png", ".jpeg", ".webp"]:
                test_path = os.path.join(images_dir, f"{img_id}{ext}")
                if os.path.exists(test_path):
                    img_path = test_path
                    break
            
            if img_path:
                st.image(img_path, caption=f"Vista oficial: {img_id}", use_column_width=True)
            else:
                st.info(f"📸 *[Vista de catálogo solicitada: {img_id}]*")
                st.image(
                    "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800&q=80",
                    caption=f"Fotografía del resort (ID: {img_id})",
                    use_column_width=True
                )

# Dibujar mensajes en la pantalla principal
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🌙" if message["role"] == "assistant" else "🧑"):
        if message["role"] == "assistant":
            render_message_with_images(message["content"])
        else:
            st.markdown(message["content"])

# Entrada de texto del usuario
if prompt := st.chat_input("Escriba su pregunta o pida ver una instalación..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
        
    with st.chat_message("assistant", avatar="🌙"):
        with st.spinner("Consultando manuales y cotizando..."):
            history_formatted = [
                (msg["role"], msg["content"]) for msg in st.session_state.messages[:-1]
            ]
            response_data = rag_engine.ask(prompt, chat_history=history_formatted)
            bot_reply = response_data["answer"]
            
            render_message_with_images(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})