"""Envía respuestas.json a la API del curso y muestra la calificación.

Uso:
    python enviar.py TU_USUARIO_HF https://huggingface.co/spaces/TU_USUARIO_HF/NOMBRE_DEL_SPACE/tree/main
"""
import json
import sys
from pathlib import Path

import requests

from herramientas import API

usuario, link_codigo = sys.argv[1], sys.argv[2]
respuestas = json.loads((Path(__file__).parent / "respuestas.json").read_text(encoding="utf-8"))

datos = {
    "username": usuario,
    "agent_code": link_codigo,
    "answers": [{"task_id": t, "submitted_answer": r} for t, r in respuestas.items()],
}
r = requests.post(f"{API}/submit", json=datos, timeout=60)
print(json.dumps(r.json(), ensure_ascii=False, indent=2))
