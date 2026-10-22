
# Imagen ligera de Python con version fija.
FROM python:3.12.12-slim-bookworm

# Configuracion del entorno.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo.
WORKDIR /app

# Crear usuario sin privilegios de administrador.
RUN groupadd --system appgroup && useradd --system --gid appgroup --home-dir /app appuser

# Copiar dependencias.
COPY requirements.txt ./

# Instalar dependencias.
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copiar script y prompts.
COPY --chown=appuser:appgroup src/inference.py ./inference.py
COPY --chown=appuser:appgroup prompts/ ./prompts/

# Crear carpeta de resultados y asignar permisos.
RUN mkdir -p /app/results && chown -R appuser:appgroup /app/results

# Ejecutar como usuario sin privilegios.
USER appuser

# Ejecutar el script.
ENTRYPOINT ["python", "inference.py"]
