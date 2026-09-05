import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def probar():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resultado = await session.list_tools()
            print([t.name for t in resultado.tools])

asyncio.run(probar())