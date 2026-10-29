"""Corre el agente sobre las 20 preguntas de GAIA y guarda las respuestas en respuestas.json.

Uso:
    python agente.py            # todas las que falten
    python agente.py 3          # solo la pregunta 3 (para probar)

Modelo: Claude Sonnet 5.5 (créditos de Anthropic). Con MODELO=groq usa Groq gratis (lento).
Tope de gasto: si el costo acumulado pasa de TOPE_USD, se detiene.
"""
import json
import os
import sys
import time
from pathlib import Path

import litellm
import requests
from PIL import Image
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel, VisitWebpageTool

from herramientas import (API, buscar_wikipedia, descargar_archivo, leer_archivo, llave,
                          subtitulos_youtube)

AQUI = Path(__file__).parent
RESPUESTAS = AQUI / "respuestas.json"
TOPE_USD = 3.0

INSTRUCCIONES = """Eres un asistente que contesta preguntas difíciles de investigación.
Reglas para la respuesta final (se califica por coincidencia EXACTA):
- Llama final_answer() solo con la respuesta, sin explicación, sin unidades salvo que las pidan, sin punto final.
- Número: solo dígitos, sin comas de miles.
- Texto: lo más corto posible, sin artículos, sin abreviaturas.
- Lista: separada por comas y un espacio, en el orden que pida la pregunta.
- Respeta el formato que pida la pregunta (orden alfabético, solo el nombre, etc.).
- Contesta en el idioma de la pregunta (casi siempre inglés).
Antes de contestar, verifica el dato en una fuente (Wikipedia, página web, archivo o video).
Usa nombres de variables cortos."""

GROQ = os.environ.get("MODELO") == "groq"
if GROQ:
    MODEL_ID = "groq/qwen/qwen3.8-27b"
    model = LiteLLMModel(model_id=MODEL_ID, api_key=llave("GROQ_API_KEY"),
                         num_retries=3, max_tokens=1000)
else:
    MODEL_ID = "anthropic/claude-sonnet-5-5"
    model = LiteLLMModel(model_id=MODEL_ID, api_key=llave("ANTHROPIC_API_KEY"),
                         num_retries=3, max_tokens=2000)


def recortar_memoria(paso, agent):
    """Recorta las observaciones viejas para gastar menos tokens.
    Con Groq gratis (8,000 tokens por minuto) además espera entre pasos."""
    pasos = [p for p in agent.memory.steps if getattr(p, "observations", None)]
    for p in pasos[:-1]:
        if len(p.observations) > 400:
            p.observations = p.observations[:400] + " …(recortado)"
    if GROQ:
        time.sleep(45)


agente = CodeAgent(
    tools=[DuckDuckGoSearchTool(max_results=4), VisitWebpageTool(max_output_length=5000),
           buscar_wikipedia, leer_archivo, subtitulos_youtube],
    model=model,
    instructions=INSTRUCCIONES,
    additional_authorized_imports=["pandas", "math", "datetime", "re", "json", "collections"],
    max_steps=8,
    step_callbacks=[recortar_memoria],
)


def costo(uso):
    precio = litellm.model_cost.get(MODEL_ID.split("/")[-1], {})
    return (uso.input_tokens * precio.get("input_cost_per_token", 0)
            + uso.output_tokens * precio.get("output_cost_per_token", 0))


def main():
    preguntas = requests.get(f"{API}/questions", timeout=30).json()
    hechas = json.loads(RESPUESTAS.read_text(encoding="utf-8")) if RESPUESTAS.exists() else {}
    solo = int(sys.argv[1]) if len(sys.argv) > 1 else None
    gastado = 0.0

    for n, p in enumerate(preguntas, start=1):
        if solo and n != solo:
            continue
        if not solo and p["task_id"] in hechas:
            continue
        if gastado >= TOPE_USD:
            print(f"\nTope de gasto alcanzado (${gastado:.2f}). Me detengo.")
            break
        texto = p["question"]
        imagenes = None
        if p.get("file_name"):
            try:
                ruta = descargar_archivo(p["task_id"], p["file_name"])
            except requests.HTTPError as e:
                print(f"\nPregunta {n}: no se pudo bajar su archivo ({e.response.status_code}). La salto.")
                continue
            if ruta.suffix.lower() in (".png", ".jpg", ".jpeg") and not GROQ:
                imagenes = [Image.open(ruta)]
                texto += "\n\nLa imagen adjunta está incluida en este mensaje."
            else:
                texto += f"\n\nArchivo adjunto: {ruta} (léelo con leer_archivo)"
        print(f"\n===== Pregunta {n}/20 =====\n{texto[:300]}")
        try:
            respuesta = str(agente.run(texto, images=imagenes)).strip()
        except Exception as e:
            print(f"Error en la pregunta {n}: {e}")
            continue
        finally:
            gastado += costo(agente.monitor.get_total_token_counts())
            print(f"--- gasto acumulado: ${gastado:.2f}")
        hechas[p["task_id"]] = respuesta
        RESPUESTAS.write_text(json.dumps(hechas, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f">>> Respuesta {n}: {respuesta}")
        if GROQ:
            time.sleep(45)

    print(f"\nListo: {len(hechas)}/20 respuestas en {RESPUESTAS.name} · gasto ${gastado:.2f}")


if __name__ == "__main__":
    main()
