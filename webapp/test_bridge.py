import asyncio, os
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from mcp_bridge import ejecutar_conversacion

load_dotenv()

async def main():
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    messages = [{"role": "user", "content": "¿Qué clientes tienes en Odoo?"}]
    texto, herramientas = await ejecutar_conversacion(client, "claude-sonnet-5", messages)
    print("--- RESPUESTA ---")
    print(texto)
    print("--- HERRAMIENTAS USADAS ---")
    print(herramientas)

asyncio.run(main())