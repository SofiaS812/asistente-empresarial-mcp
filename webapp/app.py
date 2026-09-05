import os
import asyncio
import uuid
from flask import Flask, request, jsonify, render_template
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from mcp_bridge import ejecutar_conversacion

load_dotenv()

app = Flask(__name__)

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
client_anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Historial de conversación en memoria, separado por sesión de navegador.
conversaciones: dict[str, list] = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    datos = request.get_json(force=True)
    mensaje_usuario = (datos.get("message") or "").strip()
    session_id = datos.get("session_id") or str(uuid.uuid4())

    if not mensaje_usuario:
        return jsonify({"error": "El mensaje no puede estar vacío."}), 400

    historial = conversaciones.get(session_id, [])
    historial.append({"role": "user", "content": mensaje_usuario})

    try:
        texto_final, herramientas_usadas = asyncio.run(
            ejecutar_conversacion(client_anthropic, ANTHROPIC_MODEL, historial)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al procesar la solicitud: {e}"}), 500

    historial.append({"role": "assistant", "content": texto_final})
    conversaciones[session_id] = historial

    return jsonify({
        "reply": texto_final,
        "tools_used": herramientas_usadas,
        "session_id": session_id
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)