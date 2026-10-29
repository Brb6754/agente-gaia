"""Herramientas del agente GAIA: archivos de la pregunta, Wikipedia, YouTube y audio."""
import os
import winreg
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from smolagents import tool

API = "https://agents-course-unit4-scoring.hf.space"
CARPETA_ARCHIVOS = Path(__file__).parent / "archivos"


def llave(nombre: str) -> str:
    """Lee la llave de las variables de entorno (o del registro de Windows si la terminal es vieja)."""
    if os.environ.get(nombre):
        return os.environ[nombre]
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        return winreg.QueryValueEx(k, nombre)[0]


def descargar_archivo(task_id: str, file_name: str) -> Path:
    CARPETA_ARCHIVOS.mkdir(exist_ok=True)
    ruta = CARPETA_ARCHIVOS / file_name
    if not ruta.exists():
        # la API del curso a veces da 404; respaldo: el dataset GAIA (pide aceptar sus términos en HF)
        r = requests.get(f"{API}/files/{task_id}", timeout=60)
        if r.status_code != 200:
            url = ("https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/"
                   f"2023/validation/{file_name}")
            r = requests.get(url, headers={"Authorization": f"Bearer {llave('HF_TOKEN')}"}, timeout=60)
        r.raise_for_status()
        ruta.write_bytes(r.content)
    return ruta


@tool
def leer_archivo(ruta: str) -> str:
    """Lee el archivo adjunto a la pregunta y regresa su contenido como texto.
    Soporta Excel (.xlsx), CSV, código o texto (.py, .txt, .json) y audio (.mp3, .wav), que se transcribe.

    Args:
        ruta: ruta del archivo que viene en la pregunta.
    """
    p = Path(ruta)
    ext = p.suffix.lower()
    if ext in (".xlsx", ".xls"):
        hojas = pd.read_excel(p, sheet_name=None)
        texto = "\n\n".join(f"Hoja {n}:\n{df.to_csv(index=False)}" for n, df in hojas.items())
    elif ext == ".csv":
        texto = pd.read_csv(p).to_csv(index=False)
    elif ext in (".mp3", ".wav", ".m4a"):
        texto = transcribir_audio(p)
    elif ext in (".png", ".jpg", ".jpeg"):
        texto = "Es una imagen y este agente no puede verla."
    else:
        texto = p.read_text(encoding="utf-8", errors="replace")
    return texto[:MAX_CARACTERES]


def transcribir_audio(p: Path) -> str:
    """Whisper en Groq (gratis)."""
    with open(p, "rb") as f:
        r = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {llave('GROQ_API_KEY')}"},
            files={"file": (p.name, f)},
            data={"model": "whisper-large-v3"},
            timeout=120,
        )
    r.raise_for_status()
    return r.json()["text"]


MAX_CARACTERES = 5000  # Groq gratis: 8,000 tokens por minuto; cada observación debe ser chica


@tool
def buscar_wikipedia(titulo: str, palabra: str) -> str:
    """Busca dentro de un artículo de Wikipedia en inglés y regresa solo los párrafos y filas
    de tablas que contienen la palabra. Úsala para discografías, listas, deportes y datos históricos.

    Args:
        titulo: título del artículo, por ejemplo "Mercedes Sosa".
        palabra: palabra a buscar dentro del artículo, por ejemplo "Studio albums" o "2005".
    """
    url = f"https://en.wikipedia.org/wiki/{titulo.replace(' ', '_')}"
    cabeceras = {"User-Agent": "agente-gaia-curso/1.0 (estudiante)"}
    html = requests.get(url, headers=cabeceras, timeout=30).text
    from markdownify import markdownify
    texto = markdownify(html, strip=["a", "img"])
    bloques = [b.strip() for b in texto.split("\n\n") if b.strip()]
    clave = palabra.lower()
    # cada bloque que contiene la palabra, más el siguiente (suele ser la lista o tabla)
    encontrados = []
    for i, b in enumerate(bloques):
        if clave in b.lower():
            encontrados.append(b)
            if i + 1 < len(bloques):
                encontrados.append(bloques[i + 1])
    if not encontrados:
        return f"'{palabra}' no aparece. Encabezados del artículo: " + ", ".join(
            b.strip("# ") for b in bloques if b.startswith("#"))[:MAX_CARACTERES]
    return "\n\n".join(dict.fromkeys(encontrados))[:MAX_CARACTERES]


@tool
def subtitulos_youtube(url: str) -> str:
    """Regresa los subtítulos (lo que se dice) de un video de YouTube.

    Args:
        url: link del video de YouTube.
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    video_id = url.split("v=")[-1].split("&")[0]
    try:
        partes = YouTubeTranscriptApi().fetch(video_id)
        return " ".join(p.text for p in partes)[:MAX_CARACTERES]
    except Exception as e:
        return f"No se pudieron obtener subtítulos: {e}"
