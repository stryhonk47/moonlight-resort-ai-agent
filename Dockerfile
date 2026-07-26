# 1. Imagen base oficial de Python ligera
FROM python:3.10-slim

# 2. Configurar directorio de trabajo en el contenedor
WORKDIR /app

# 3. Instalar herramientas del sistema necesarias para compilar dependencias de IA
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar dependencias (aprovechando el caché de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar todo el código fuente y el catálogo visual/PDFs
COPY . .

# 6. MÁGIA RAG: Ingestar los PDFs y crear la base de datos vectorial local dentro del contenedor
RUN python src/backend/document_loader.py

# 7. Exponer el puerto predeterminado de Streamlit
EXPOSE 8501

# 8. Variable de entorno para que Streamlit corra sin pedir confirmaciones de email en producción
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 9. Comando de arranque del servidor web
CMD ["streamlit", "run", "src/frontend/app.py"]