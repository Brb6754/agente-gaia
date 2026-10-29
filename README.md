# Agente GAIA · Unidad 4 del curso de Agents de Hugging Face

Meta: **6 de 20 o más (30%)** para el certificado de completion.

## Archivos
| Archivo | Qué hace |
|---|---|
| `herramientas.py` | Tools: leer archivo adjunto (Excel, código, audio con Whisper de Groq), Wikipedia con tablas, subtítulos de YouTube |
| `agente.py` | CodeAgent con Claude Sonnet 5.5 (o Groq gratis con `MODELO=groq`) + búsqueda web; contesta y guarda en `respuestas.json`, con tope de gasto |
| `enviar.py` | Manda `respuestas.json` a la API del curso y muestra tu calificación |
| `preguntas.json` | Copia de las 20 preguntas |

## Pasos
1. Abre una terminal en esta carpeta y activa el entorno:
   `.venv\Scripts\activate`
2. Prueba una sola pregunta (la 3 es fácil):
   `python agente.py 3`
3. Corre todas (tarda; si Groq te frena, vuelve a correrlo y sigue donde se quedó):
   `python agente.py`
4. Revisa `respuestas.json`. Si alguna salió con explicación en vez de solo la respuesta, corrígela a mano o vuelve a correr esa pregunta: `python agente.py 7`
5. En Hugging Face: duplica el Space del template del curso (`agents-course/Final_Assignment_Template`) a tu perfil, **público**, y sube estos archivos.
6. Envía:
   `python enviar.py TU_USUARIO https://huggingface.co/spaces/TU_USUARIO/TU_SPACE/tree/main`
7. Si sale 30% o más: página del certificado → inicia sesión → nombre completo → **Get My Certificate**.

## Qué no puede hacer (y está bien)
- Ver imágenes (pregunta del ajedrez): Groq gratis no tiene modelo de visión.
- Ver videos sin subtítulos (la de los pájaros).
Con 6 buenas de las otras 18 alcanza.
