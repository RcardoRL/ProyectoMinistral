
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

CARPETA = Path(__file__).resolve().parent.parent
ARCHIVO_PROMPTS = CARPETA / "prompts" / "suite.json"
ARCHIVO_RESULTADOS = CARPETA / "results" / "resultados_suite.json"

MODELO = "ministral-3:8b"
URL_API = "http://localhost:11434/api/chat"


def consultar_modelo(instruccion, temperatura=0.9):
    """Envía una instrucción a Ollama y devuelve la respuesta."""
    datos = {
        "model": MODELO,
        "messages": [
            {"role": "user", "content": instruccion}
        ],
        "stream": False,
        "options": {"temperature": temperatura}
    }

    contenido = json.dumps(datos).encode("utf-8")
    solicitud = urllib.request.Request(
        URL_API,
        data=contenido,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(solicitud, timeout=600) as respuesta:
        resultado = json.loads(respuesta.read().decode("utf-8"))

    return resultado["message"]["content"]


def main():
    with open(ARCHIVO_PROMPTS, "r", encoding="utf-8-sig") as archivo:
        suite = json.load(archivo)

    resultados = []

    print(f"Modelo: {MODELO}")
    print(f"Cantidad de prompts: {len(suite['prompts'])}")
    print("Iniciando pruebas...\n")

    for prompt in suite["prompts"]:
        print(
            f"Ejecutando prompt {prompt['id']}/"
            f"{len(suite['prompts'])}: {prompt['categoria']}"
        )

        try:
            respuesta = consultar_modelo(prompt["instruccion"])
            print(respuesta)

            resultados.append({
                "id": prompt["id"],
                "categoria": prompt["categoria"],
                "instruccion": prompt["instruccion"],
                "temperatura": 0.9,
                "respuesta": respuesta,
                "evaluacion": "",
                "justificacion": ""
            })

        except (urllib.error.URLError, TimeoutError, KeyError,
                json.JSONDecodeError) as error:
            print(f"Error técnico: {error}")

            resultados.append({
                "id": prompt["id"],
                "categoria": prompt["categoria"],
                "instruccion": prompt["instruccion"],
                "temperatura": 0.9,
                "respuesta": "",
                "evaluacion": "error_tecnico",
                "justificacion": str(error)
            })

        print("\n" + "-" * 60 + "\n")

    documento = {
        "modelo": MODELO,
        "fecha_ejecucion": datetime.now().astimezone().isoformat(),
        "resultados": resultados
    }

    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as archivo:
        json.dump(documento, archivo, ensure_ascii=False, indent=2)

    print(f"Pruebas finalizadas. Resultados guardados en:\n{ARCHIVO_RESULTADOS}")


if __name__ == "__main__":
    main()