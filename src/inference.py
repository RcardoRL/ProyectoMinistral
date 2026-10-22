"""
Script propio de inferencia para modelos locales mediante Ollama.

Permite ejecutar un prompt individual o una suite desde un archivo JSON.
Guarda los resultados en JSON y CSV, incluyendo tiempos, TTFT y tokens/segundo.
"""

import argparse
import csv
import json
import sys
import time
import os

from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# Dirección local de la API de Ollama. No requiere credenciales.
#OLLAMA_URL = "http://127.0.0.1:11434"

# Dirección configurable de Ollama para Windows y Docker.

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://127.0.0.1:11434"
)


def consultar_api(endpoint, datos=None, timeout=30):
    """Realiza una petición HTTP a la API local de Ollama."""
    url = f"{OLLAMA_URL}{endpoint}"
    cuerpo = None
    encabezados = {}

    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        encabezados["Content-Type"] = "application/json"

    solicitud = Request(
        url,
        data=cuerpo,
        headers=encabezados,
        method="POST" if datos is not None else "GET",
    )

    with urlopen(solicitud, timeout=timeout) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def verificar_modelo(modelo):
    """Comprueba que Ollama esté activo y que el modelo esté instalado."""
    try:
        datos = consultar_api("/api/tags")
    except (URLError, TimeoutError, OSError) as error:
        raise RuntimeError(
            "No se pudo conectar con Ollama. "
            "Comprueba que Ollama esté abierto y funcionando."
        ) from error

    modelos_instalados = {
        elemento.get("name")
        for elemento in datos.get("models", [])
    }

    if modelo not in modelos_instalados:
        disponibles = ", ".join(sorted(modelos_instalados)) or "ninguno"
        raise RuntimeError(
            f"El modelo '{modelo}' no está instalado con ese nombre. "
            f"Modelos disponibles: {disponibles}. "
            "Comprueba el nombre con el comando 'ollama list'."
        )


def cargar_prompts(archivo=None, prompt_individual=None):
    """Carga un prompt individual o una lista de prompts desde JSON."""
    if prompt_individual:
        return [{
            "id": 1,
            "categoria": "prompt_individual",
            "instruccion": prompt_individual,
        }]

    ruta = Path(archivo)

    if not ruta.is_file():
        raise RuntimeError(f"No se encontró el archivo: {ruta}")

    try:
        with ruta.open("r", encoding="utf-8") as entrada:
            datos = json.load(entrada)
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(
            f"No se pudo leer el archivo JSON: {error}"
        ) from error

    # Admite una lista directa o un objeto con "prompts" o "resultados".
    if isinstance(datos, dict):
        datos = datos.get("prompts", datos.get("resultados"))

    if not isinstance(datos, list) or not datos:
        raise RuntimeError(
            "El archivo debe contener una lista de prompts "
            "o una propiedad 'prompts'/'resultados' con una lista."
        )

    prompts = []

    for indice, elemento in enumerate(datos, start=1):
        if isinstance(elemento, str):
            texto = elemento
            identificador = indice
            categoria = "sin_categoria"
        elif isinstance(elemento, dict):
            texto = (
                elemento.get("instruccion")
                or elemento.get("prompt")
                or elemento.get("texto")
            )
            identificador = elemento.get("id", indice)
            categoria = elemento.get("categoria", "sin_categoria")
        else:
            continue

        if isinstance(texto, str) and texto.strip():
            prompts.append({
                "id": identificador,
                "categoria": categoria,
                "instruccion": texto.strip(),
            })

    if not prompts:
        raise RuntimeError(
            "No se encontraron prompts válidos. "
            "Cada elemento debe incluir 'instruccion', 'prompt' o 'texto'."
        )

    return prompts


def ejecutar_inferencia(modelo, prompt, temperatura, max_tokens):
    """
    Ejecuta una inferencia en modo streaming.

    TTFT: tiempo hasta recibir el primer fragmento de texto no vacío.
    tokens_por_segundo: tokens generados / duración de generación
    informada por Ollama.
    """
    solicitud = {
        "model": modelo,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperatura,
            "num_predict": max_tokens,
        },
    }

    cuerpo = json.dumps(solicitud).encode("utf-8")
    peticion = Request(
        f"{OLLAMA_URL}/api/generate",
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    inicio = time.perf_counter()
    primer_fragmento = None
    fragmentos = []
    datos_finales = {}

    try:
        with urlopen(peticion, timeout=600) as respuesta_http:
            for linea in respuesta_http:
                if not linea.strip():
                    continue

                evento = json.loads(linea.decode("utf-8"))

                if evento.get("error"):
                    raise RuntimeError(evento["error"])

                fragmento = evento.get("response", "")

                if fragmento:
                    if primer_fragmento is None:
                        primer_fragmento = time.perf_counter()
                    fragmentos.append(fragmento)

                if evento.get("done"):
                    datos_finales = evento
                    break

    except HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Ollama devolvió el error HTTP {error.code}: {detalle}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            "Se perdió la conexión con Ollama durante la inferencia."
        ) from error

    fin = time.perf_counter()
    salida = "".join(fragmentos)

    # Convierte nanosegundos de Ollama a segundos.
    duracion_generacion = (
        datos_finales.get("eval_duration", 0) / 1_000_000_000
    )
    tokens_generados = datos_finales.get("eval_count", 0)

    # Usa la duración reportada por Ollama para calcular tokens/segundo.
    if duracion_generacion > 0:
        tokens_por_segundo = tokens_generados / duracion_generacion
    else:
        tokens_por_segundo = 0.0

    ttft = (
        primer_fragmento - inicio
        if primer_fragmento is not None
        else None
    )

    return {
        "salida": salida,
        "tokens_generados": tokens_generados,
        "tokens_entrada": datos_finales.get("prompt_eval_count", 0),
        "ttft_segundos": round(ttft, 4) if ttft is not None else None,
        "tiempo_total_segundos": round(fin - inicio, 4),
        "tiempo_generacion_segundos": round(duracion_generacion, 4),
        "tokens_por_segundo": round(tokens_por_segundo, 4),
        "error": "",
    }


def main():
    """Procesa los argumentos, ejecuta los prompts y guarda los resultados."""
    parser = argparse.ArgumentParser(
        description="Script de inferencia local para Ollama."
    )

    parser.add_argument(
        "--modelo",
        default="ministral-3:8b",
        help="Nombre del modelo instalado en Ollama.",
    )

    origen = parser.add_mutually_exclusive_group(required=True)
    origen.add_argument(
        "--prompt",
        help="Texto de un prompt individual.",
    )
    origen.add_argument(
        "--archivo",
        help="Ruta relativa o accesible a un archivo JSON de prompts.",
    )

    parser.add_argument(
        "--temperatura",
        type=float,
        default=0.2,
        help="Temperatura del modelo (por defecto: 0.2).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Máximo de tokens nuevos (por defecto: 512).",
    )

    args = parser.parse_args()

    if not 0 <= args.temperatura <= 2:
        parser.error("La temperatura debe estar entre 0 y 2.")

    if args.max_tokens < 1:
        parser.error("--max-tokens debe ser mayor que cero.")

    try:
        verificar_modelo(args.modelo)
        prompts = cargar_prompts(args.archivo, args.prompt)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
    except HTTPError as error:
        print(
            f"ERROR: Ollama devolvió HTTP {error.code}.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Crea results/ dentro del proyecto, sin depender de una ruta absoluta.
    carpeta_resultados = Path(__file__).resolve().parent / "results"
    carpeta_resultados.mkdir(parents=True, exist_ok=True)

    resultados = []
    print(f"Modelo: {args.modelo}")
    print(f"Prompts por ejecutar: {len(prompts)}")
    print(f"Temperatura: {args.temperatura}")
    print(f"Máximo de tokens: {args.max_tokens}")

    for numero, elemento in enumerate(prompts, start=1):
        prompt = elemento["instruccion"]
        print(f"\n[{numero}/{len(prompts)}] Ejecutando prompt...")

        registro = {
            "id": elemento["id"],
            "categoria": elemento["categoria"],
            "modelo": args.modelo,
            "temperatura": args.temperatura,
            "max_tokens": args.max_tokens,
            "prompt": prompt,
        }

        try:
            registro.update(
                ejecutar_inferencia(
                    args.modelo,
                    prompt,
                    args.temperatura,
                    args.max_tokens,
                )
            )
            print(
                f"  Tokens: {registro['tokens_generados']} | "
                f"TTFT: {registro['ttft_segundos']} s | "
                f"Tokens/s: {registro['tokens_por_segundo']}"
            )
        except (RuntimeError, HTTPError, URLError, TimeoutError, OSError) as error:
            registro.update({
                "salida": "",
                "tokens_generados": 0,
                "tokens_entrada": 0,
                "ttft_segundos": None,
                "tiempo_total_segundos": 0,
                "tiempo_generacion_segundos": 0,
                "tokens_por_segundo": 0,
                "error": str(error),
            })
            print(f"  ERROR: {error}", file=sys.stderr)

        resultados.append(registro)

    # Usa fecha y hora para no sobrescribir ejecuciones anteriores.
    marca_tiempo = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    archivo_json = carpeta_resultados / f"resultados_{marca_tiempo}.json"
    archivo_csv = carpeta_resultados / f"resultados_{marca_tiempo}.csv"

    documento = {
        "modelo": args.modelo,
        "fecha_ejecucion": datetime.now().astimezone().isoformat(),
        "temperatura": args.temperatura,
        "max_tokens": args.max_tokens,
        "cantidad_prompts": len(prompts),
        "resultados": resultados,
    }

    with archivo_json.open("w", encoding="utf-8") as salida_json:
        json.dump(documento, salida_json, ensure_ascii=False, indent=2)

    columnas = [
        "id", "categoria", "modelo", "temperatura", "max_tokens",
        "prompt", "salida", "tokens_generados", "tokens_entrada",
        "ttft_segundos", "tiempo_total_segundos",
        "tiempo_generacion_segundos", "tokens_por_segundo", "error",
    ]

    with archivo_csv.open(
        "w", newline="", encoding="utf-8-sig"
    ) as salida_csv:
        escritor = csv.DictWriter(salida_csv, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(resultados)

    errores = sum(bool(item.get("error")) for item in resultados)
    print("\nEjecución finalizada.")
    print(f"Resultados JSON: {archivo_json}")
    print(f"Resultados CSV:  {archivo_csv}")
    print(f"Prompts con error: {errores} de {len(resultados)}")


if __name__ == "__main__":
    main()