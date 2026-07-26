import os
import re
import sys
import streamlit as st

# Añadir el directorio raíz al path para poder importar nuestro backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from src.backend.rag_pipeline import MoonlightRAG

# Configuración de la página en Streamlit
st.set_page_config(
    page_title="Moonlight Resort - Conserje IA",
    page_icon="🌙",
    layout="centered"
)

# Estilos CSS personalizados para darle un toque elegante y limpio
st.markdown("""
<style>
    .chat-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .resort-title {
        color: #1E3A8A;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado visual
st.markdown("<div class='chat-header'><h1 class='resort-title'>🌙 Moonlight Resort</h1><p>Asistente Virtual y Conserje de Lujo (Powered by RAG & Cohere)</p></div>", unsafe_allow_html=True)

# Inicialización en caché del motor RAG para no recargar la base de datos en cada clic
@st.cache_resource(show_spinner="Cargando base de datos del resort y conectando a Cohere...")
def get_rag_engine():
    return MoonlightRAG()

try:
    rag_engine = get_rag_engine()
except Exception as e:
    st.error(f"❌ Error fatal al iniciar el motor IA: {str(e)}")
    st.stop()

# Manejo del historial de conversación en la sesión de Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy el conserje digital de Moonlight Resort 🌴. ¿En qué puedo ayudarle hoy? Puedo informarle sobre nuestras habitaciones, realizar cotizaciones, explicarle nuestras normas o mostrarle fotografías de nuestras instalaciones."}
    ]

# Función para extraer etiquetas [ID_IMAGEN: X] y mostrar la imagen real
def render_message_with_images(text: str):
    # Expresión regular para buscar el patrón [ID_IMAGEN: NOMBRE_EXACTO]
    pattern = r"\[ID_IMAGEN:\s*([A-Za-z0-9_]+)\]"
    matches = re.findall(pattern, text)
    
    # Eliminamos la etiqueta del texto para que el cliente no vea el código técnico
    clean_text = re.sub(pattern, "", text).strip()
    
    # Mostramos el texto limpio de la respuesta
    st.markdown(clean_text)
    
    # Si detectamos etiquetas de imágenes, las renderizamos debajo del texto
    if matches:
        images_dir = os.path.join(BASE_DIR, "data", "images")
        for img_id in matches:
            # Buscamos si la imagen existe con varias extensiones (.jpg, .png, .jpeg)
            img_path = None
            for ext in [".jpg", ".png", ".jpeg", ".webp"]:
                test_path = os.path.join(images_dir, f"{img_id}{ext}")
                if os.path.exists(test_path):
                    img_path = test_path
                    break
            
            # Si el archivo está en data/images/, lo mostramos
            if img_path:
                st.image(img_path, caption=f"Vista oficial: {img_id}", use_column_width=True)
            else:
                # Fallback visual de prueba por si aún no guardaste la foto en local
                st.info(f"📸 *[Vista de catálogo solicitada: {img_id}]*")
                # Mostramos una foto tropical de Unsplash temporalmente para la demo
                st.image(
                    "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800&q=80",
                    caption=f"Fotografía del resort (ID: {img_id})",
                    use_column_width=True
                )

# Dibuja los mensajes históricos en pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🌙" if message["role"] == "assistant" else "🧑"):
        if message["role"] == "assistant":
            render_message_with_images(message["content"])
        else:
            st.markdown(message["content"])

# Entrada de chat del usuario (Chat Input)
if prompt := st.chat_input("Escriba su pregunta o pida ver una instalación..."):
    # Mostrar mensaje del usuario en pantalla
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
        
    # Generar respuesta con el motor RAG
    with st.chat_message("assistant", avatar="🌙"):
        with st.spinner("Consultando manuales y cotizando..."):
            # Preparamos el historial para enviarlo al backend
            history_formatted = [
                (msg["role"], msg["content"]) for msg in st.session_state.messages[:-1]
            ]
            
            # Consultamos a Cohere Command R+
            response_data = rag_engine.ask(prompt, chat_history=history_formatted)
            bot_reply = response_data["answer"]
            
            # Renderizamos la respuesta y la foto en tiempo real
            render_message_with_images(bot_reply)
            
            # Guardamos en el historial
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})