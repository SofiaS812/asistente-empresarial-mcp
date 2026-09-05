import os
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")


def _tool_mcp_a_anthropic(tool) -> dict:
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.inputSchema or {"type": "object", "properties": {}},
    }


def _texto_resultado_tool(resultado) -> str:
    partes = []
    for bloque in resultado.content:
        texto = getattr(bloque, "text", None)
        partes.append(texto if texto else str(bloque))
    texto_final = "\n".join(partes) if partes else "(sin contenido)"
    if getattr(resultado, "isError", False):
        return f"ERROR reportado por la herramienta: {texto_final}"
    return texto_final


async def _con_reintentos(func, intentos=3, espera=1.0):
    """Reintenta una operación de red contra el servidor MCP ante fallos de conexión intermitentes."""
    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            return await func()
        except Exception as e:
            ultimo_error = e
            print(f"[MCP] Intento {intento}/{intentos} falló: {e}")
            await asyncio.sleep(espera)
    raise ultimo_error


async def _listar_tools_anthropic() -> list:
    async def intento():
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                resultado = await session.list_tools()
                return [_tool_mcp_a_anthropic(t) for t in resultado.tools]
    return await _con_reintentos(intento)


async def _llamar_tool(nombre: str, argumentos: dict) -> str:
    async def intento():
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                resultado = await session.call_tool(nombre, argumentos)
                return _texto_resultado_tool(resultado)
    return await _con_reintentos(intento)

async def ejecutar_conversacion(client_anthropic, model: str, messages: list) -> tuple[str, list]:
    """
    Envía la conversación a Claude. Si Claude pide usar una herramienta MCP,
    la ejecuta contra el servidor real (en una conexión corta e independiente)
    y le devuelve el resultado, repitiendo hasta obtener una respuesta final en texto.
    """
    herramientas_usadas = []
    tools = await _listar_tools_anthropic()

    respuesta = await client_anthropic.messages.create(
        model=model,
        max_tokens=1500,
        tools=tools,
        messages=messages,
    )

    while respuesta.stop_reason == "tool_use":
        bloques_tool = [b for b in respuesta.content if b.type == "tool_use"]
        messages.append({"role": "assistant", "content": respuesta.content})

        resultados_tool = []
        for bloque in bloques_tool:
            herramientas_usadas.append({
                "nombre": bloque.name,
                "parametros": bloque.input
            })
            texto_resultado = await _llamar_tool(bloque.name, bloque.input)
            resultados_tool.append({
                "type": "tool_result",
                "tool_use_id": bloque.id,
                "content": texto_resultado,
            })

        messages.append({"role": "user", "content": resultados_tool})

        respuesta = await client_anthropic.messages.create(
            model=model,
            max_tokens=1500,
            tools=tools,
            messages=messages,
        )

    texto_final = "".join(
        b.text for b in respuesta.content if b.type == "text"
    )
    return texto_final, herramientas_usadas