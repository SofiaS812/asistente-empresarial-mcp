# Asistente Empresarial Inteligente basado en Model Context Protocol (MCP)

Proyecto de la asignatura **Sistemas Distribuidos**. Implementa un asistente empresarial que permite consultar y ejecutar operaciones sobre distintos sistemas de información (ERP, correo electrónico y una API pública) mediante lenguaje natural, usando **exclusivamente** el protocolo **MCP** como mecanismo de integración entre el modelo de lenguaje y los sistemas empresariales.

## Evaluación / Sustentación

- 📄 **Plan de pruebas:** [`Plan_de_Pruebas_y_Guion_Sustentacion.docx`](./Plan_de_Pruebas_y_Guion_Sustentacion.docx) — tabla con los 21 ítems evaluados, pasos de prueba y resultados.
- 🎥 **Video de sustentación (ejecución del plan de pruebas):** [enlace a YouTube](PEGAR_AQUÍ_EL_ENLACE)

## Arquitectura

```
Claude Desktop (cliente MCP)
        │  HTTP → puerto 8000
        ▼
Contenedor mcp-server (servidor MCP en Python / FastMCP)
        │ XML-RPC        │ REST (OAuth2)     │ HTTPS
        ▼                ▼                    ▼
Contenedor odoo    Gmail API (externa)   API pública TRM (datos.gov.co)
        │
        ▼
Contenedor db (PostgreSQL)
```

**Principio de diseño:** el modelo de lenguaje no tiene acceso directo a Odoo, PostgreSQL, Gmail ni a la API de TRM. Toda interacción pasa exclusivamente por las herramientas expuestas por el servidor MCP.

## Estructura del repositorio

```
proyecto-mcp-odoo/
├── docker-compose.yml
├── Plan_de_Pruebas_y_Guion_Sustentacion.docx
├── odoo/addons/
└── mcp-server/
    ├── Dockerfile
    ├── requirements.txt
    ├── .env.example        # plantilla de variables de entorno (sin valores reales)
    ├── server.py
    ├── tools/
    │   ├── odoo_client.py / odoo_tools.py
    │   ├── gmail_client.py / gmail_tools.py
    │   ├── trm_client.py / trm_tools.py
    │   ├── reportes_client.py / reportes_tools.py
    │   └── excepciones.py
    └── logs/trazabilidad.py
```

## Herramientas MCP expuestas

| Herramienta | Sistema | Descripción |
|---|---|---|
| `consultar_clientes` | Odoo | Lista de clientes |
| `consultar_productos` | Odoo | Catálogo con stock |
| `consultar_ventas` | Odoo | Órdenes de venta |
| `consultar_facturas` | Odoo | Facturas (filtro por estado) |
| `consultar_inventario` | Odoo | Existencias por producto |
| `consultar_correos_cliente` | Gmail | Correos por cliente/factura/asunto |
| `enviar_correo_cliente` | Gmail | Envío de correos |
| `consultar_trm` | API TRM | Tasa Representativa del Mercado |
| `convertir_moneda_a_cop` | API TRM | Conversión de moneda extranjera a COP |
| `generar_reporte_clientes` / `generar_reporte_facturas` | Odoo | Reportes en PDF o Excel |
| `consultar_trazabilidad` | Interno | Historial de invocaciones MCP registradas |

Cada invocación se registra automáticamente (herramienta, parámetros, duración, estado y resultado) mediante el decorador `@trazar`, persistido en SQLite.

## Cómo levantar el proyecto

1. Crear `mcp-server/.env` a partir de `mcp-server/.env.example`, con tus propios datos de Odoo.
2. Colocar `credentials.json` de Gmail (obtenido en Google Cloud Console) dentro de `mcp-server/`. `token.json` se genera solo en el primer uso.
3. Levantar todo:
   ```bash
   docker compose up -d --build
   docker compose ps   # confirmar que db, odoo y mcp-server estén "Up"
   ```
4. Acceder a Odoo en `http://localhost:8069`.
5. Conectar Claude Desktop al servidor (`http://localhost:8000/mcp`) usando el puente `mcp-remote` en `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "odoo-mcp-server": {
         "command": "npx",
         "args": ["mcp-remote", "http://localhost:8000/mcp"]
       }
     }
   }
   ```

> Ni `.env`, ni `credentials.json`, ni `token.json` están incluidos en este repositorio (excluidos en `.gitignore` por seguridad).

## Manejo de errores

Cada integración (Odoo, Gmail, TRM) devuelve un error controlado si el servicio no está disponible, en vez de un error crudo.

## Autores

Amaurys Castro De Arco
Daniel Jimenez Salcedo
Sofía Marcela Suancha Contreras
— Curso de Sistemas Distribuidos -
2026.
