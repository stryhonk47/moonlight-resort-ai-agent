import os
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.backend.prompts import SYSTEM_PROMPT

# Cargar variables de entorno (COHERE_API_KEY y CHROMA_DB_DIR)
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DB_DIR = os.path.join(BASE_DIR, os.getenv("CHROMA_DB_DIR", "chroma_db"))

class MoonlightRAG:
    def __init__(self):
        """
        Inicializa el pipeline RAG cargando la base de datos vectorial local
        y configurando el modelo LLM de Cohere bajo el estándar moderno LCEL.
        """
        if not os.path.exists(CHROMA_DB_DIR):
            raise FileNotFoundError(
                f"❌ No se encontró la base de datos en {CHROMA_DB_DIR}.\n"
                "Por favor, ejecuta primero el script: python src/backend/document_loader.py"
            )
            
        print("🧠 Cargando modelo de Embeddings Locales...")
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        print("💾 Conectando a la base de datos vectorial ChromaDB...")
        self.vector_store = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=self.embeddings
        )
        
        # Configuración del recuperador semántico para traer los 4 fragmentos más relevantes
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        
        print("🤖 Inicializando modelo Command R+ de Cohere...")
        # Utilizamos el modelo insignia de Cohere, altamente optimizado para RAG
        self.llm = ChatCohere(
            model="command-r-plus-08-2024",
            temperature=0.3
        )
        
        # Plantilla moderna con LangChain Core
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # Cadena LCEL (LangChain Expression Language) moderna y directa
        self.rag_chain = self.prompt | self.llm
        print("✅ Pipeline RAG moderno con Cohere listo y operativo.")

    def ask(self, query: str, chat_history: list = None) -> dict:
        """
        Recupera el contexto semántico en ChromaDB e invoca a Cohere Command R+.
        """
        if chat_history is None:
            chat_history = []
            
        # 1. Recuperar los documentos relevantes directamente usando el retriever
        docs = self.retriever.invoke(query)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # 2. Generar respuesta invocando la cadena con el contexto y el historial
        response = self.rag_chain.invoke({
            "context": context_text,
            "input": query,
            "chat_history": chat_history
        })
        
        # Extraer el texto limpio de la respuesta del LLM
        answer_text = response.content if hasattr(response, "content") else str(response)
        
        return {
            "answer": answer_text,
            "source_documents": docs
        }

# Bloque de prueba en terminal
if __name__ == "__main__":
    try:
        print("🚀 Iniciando prueba en terminal del conserje IA del Moonlight Resort (Powered by Cohere)...\n")
        agent = MoonlightRAG()
        
        # Prueba 1: Cotización
        q1 = "¿Cuánto cuesta la Master Suite por 2 noches y qué incluye?"
        print(f"\n🧑 💬 Usuario: {q1}")
        res1 = agent.ask(q1)
        print(f"🤖 🌙 Agente:\n{res1['answer']}\n")
        print("-" * 50)
        
        # Prueba 2: Foto y etiqueta visual
        q2 = "¿Puedes mostrarme una foto de la piscina para adultos?"
        print(f"\n🧑 💬 Usuario: {q2}")
        res2 = agent.ask(q2)
        print(f"🤖 🌙 Agente:\n{res2['answer']}\n")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución del pipeline: {str(e)}")