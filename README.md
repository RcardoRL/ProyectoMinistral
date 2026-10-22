\# Inferencia local con Ministral 3 8B utilizando Python, Ollama y Docker



\## 1. Descripción del proyecto



Este proyecto implementa un sistema de inferencia local utilizando el modelo de lenguaje \*\*Ministral 3 8B\*\*, mediante Python y Ollama.



Su objetivo es ejecutar prompts de distintas categorías, registrar las respuestas generadas y analizar el comportamiento del modelo en dos entornos de ejecución:



\- Ejecución nativa en Windows.

\- Ejecución mediante contenedores Docker.



El proyecto permite configurar la temperatura, el número máximo de tokens y el modelo utilizado. También permite ejecutar prompts individuales o una suite de pruebas almacenada en formato JSON.



Los resultados se registran en archivos CSV y JSON para facilitar su posterior análisis.



\## 2. Tecnologías utilizadas



\- Python 3.12 para el contenedor Docker.

\- Ollama para gestionar y ejecutar el modelo.

\- Ministral 3 8B como modelo de lenguaje.

\- Docker y Docker Compose para la ejecución en contenedores.

\- PowerShell para ejecutar los comandos en Windows.

\- Git y GitHub para el control de versiones.



El script de inferencia utiliza únicamente bibliotecas estándar de Python.



\## 3. Estructura del proyecto



```text

ProyectoMinistral/

├── README.md

├── requirements.txt

├── Dockerfile

├── .dockerignore

├── .gitignore

├── docker-compose.yml

├── src/

│   ├── inference.py

│   └── ejecutar\_suite.py

├── prompts/

│   └── suite.json

├── results/

│   ├── archivos CSV

│   └── archivos JSON

└── docs/

&#x20;   ├── capturas/

&#x20;   └── logs/

```



\## 4. Requisitos previos



Para reproducir el proyecto se necesita:



\- Windows con PowerShell, o un sistema compatible con Python y Docker.

\- Python 3.12 o una versión compatible.

\- Ollama instalado.

\- Docker Desktop con Docker Compose.

\- Git para clonar el repositorio.

\- Memoria RAM y almacenamiento suficientes para ejecutar Ministral 3 8B.



La disponibilidad de recursos influye en el rendimiento de la inferencia.



\## 5. Obtener el proyecto



Clonar el repositorio desde GitHub:



```powershell

git clone URL\_DEL\_REPOSITORIO

cd ProyectoMinistral

```



Sustituir `URL\_DEL\_REPOSITORIO` por la dirección del repositorio publicado.



\## 6. Descargar el modelo



Instalar Ollama desde su sitio oficial:



https://ollama.com



Descargar el modelo:



```powershell

ollama pull ministral-3:8b

```



Verificar que esté instalado:



```powershell

ollama list

```



El modelo debe aparecer con el nombre `ministral-3:8b`.



Los archivos del modelo no se incluyen en el repositorio de GitHub debido a su tamaño.



\## 7. Ejecución nativa



Abrir PowerShell desde la carpeta principal del proyecto.



Verificar que Ollama esté disponible y que el modelo esté descargado.



\### Ejecutar un prompt individual



```powershell

python .\\src\\inference.py --modelo ministral-3:8b --prompt "Explica qué es la inteligencia artificial." --temperatura 0.2 --max-tokens 100

```



\### Ejecutar un prompt de razonamiento



```powershell

python .\\src\\inference.py --modelo ministral-3:8b --prompt "Si un producto cuesta 1500 colones y tiene un descuento del 20 %, ¿cuál es su precio final?" --temperatura 0.2 --max-tokens 150

```



\### Ejecutar la suite de prompts



```powershell

python .\\src\\inference.py --modelo ministral-3:8b --archivo .\\prompts\\suite.json --temperatura 0.2 --max-tokens 512

```



Los resultados se guardan según la configuración del script de inferencia.



\## 8. Ejecución mediante Docker



El proyecto utiliza Docker Compose para configurar dos servicios:



\- `ollama`: ejecuta el servidor del modelo.

\- `inferencia`: ejecuta el script de Python.



\### Construir la imagen



```powershell

docker compose build inferencia

```



\### Iniciar Ollama



```powershell

docker compose up -d ollama

```



\### Descargar el modelo dentro del contenedor



```powershell

docker exec ministral-ollama ollama pull ministral-3:8b

```



\### Ejecutar un prompt



```powershell

docker compose run --rm inferencia --modelo ministral-3:8b --prompt "Explica qué es Docker." --temperatura 0.2 --max-tokens 100

```



\### Ejecutar la suite



```powershell

docker compose run --rm inferencia --modelo ministral-3:8b --archivo prompts/suite.json --temperatura 0.2 --max-tokens 512

```



\### Observar el consumo de recursos



En otra ventana de PowerShell:



```powershell

docker stats

```



\### Detener los servicios



```powershell

docker compose down

```



El volumen de Ollama conserva los archivos descargados del modelo.



\## 9. Ejemplo de salida



Comando:



```powershell

python .\\src\\inference.py --modelo ministral-3:8b --prompt "¿Cuánto es 5 + 7?" --temperatura 0.2 --max-tokens 50

```



Respuesta esperada:



```text

12

```



La salida real puede incluir información adicional sobre la ejecución y las métricas de desempeño.



Las respuestas del modelo pueden variar entre ejecuciones.



\## 10. Resultados



La carpeta `results/` contiene archivos CSV y JSON generados durante las pruebas.



Estos archivos permiten consultar los resultados de las ejecuciones y analizar el comportamiento del modelo.



Se incluyen resultados de diferentes corridas y registros de consumo de recursos.



\## 11. Evidencias



La carpeta `docs/` está destinada a almacenar:



\- Capturas de la ejecución nativa.

\- Capturas de la construcción y ejecución de Docker.

\- Evidencias de la utilización de recursos.

\- Registros de ejecución y pruebas.



\## 12. Control de versiones



El proyecto utiliza Git para registrar los cambios realizados durante su desarrollo.



El repositorio contiene los scripts, archivos de configuración, prompts, resultados y documentación necesarios para reproducir las pruebas.



Los archivos del modelo se excluyen mediante `.gitignore`.



