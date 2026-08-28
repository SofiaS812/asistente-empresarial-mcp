from mcp.server.fastmcp import FastMCP
from tools.odoo_client import odoo
from tools.gmail_client import enviar_correo, consultar_correos, consultar_correos_por_criterio
from tools.trm_client import consultar_trm_actual, consultar_trm_fecha, convertir_a_cop
from logs.trazabilidad import trazar, obtener_historial
from tools.reportes_client import generar_reporte_pdf, generar_reporte_excel
from tools.excepciones import OdooNoDisponibleError, GmailNoDisponibleError, TRMNoDisponibleError



mcp = FastMCP("odoo-mcp-server", host="0.0.0.0", port=8000)


@mcp.tool()
@trazar
def consultar_clientes(limite: int = 10) -> list:
    """Consulta la lista de clientes registrados en Odoo."""
    if odoo is None:
        raise OdooNoDisponibleError("El servicio no se inicializó correctamente al arrancar")
    return odoo.search_read(
        'res.partner',
        [('customer_rank', '>', 0)],
        ['name', 'email', 'phone', 'country_id'],
        limit=limite
    )

@mcp.tool()
@trazar
def consultar_productos(limite: int = 20) -> list:
    """Consulta los productos disponibles en el catálogo de Odoo, incluyendo su stock actual."""
    if odoo is None:
        raise OdooNoDisponibleError("El servicio no se inicializó correctamente al arrancar")
    return odoo.search_read(
        'product.product',
        [],
        ['name', 'list_price', 'qty_available', 'default_code'],
        limit=limite
    )

@mcp.tool()
@trazar
def consultar_ventas(limite: int = 10) -> list:
    """Consulta las órdenes de venta registradas en Odoo."""
    if odoo is None:
        raise OdooNoDisponibleError("El servicio no se inicializó correctamente al arrancar")
    return odoo.search_read(
        'sale.order',
        [],
        ['name', 'partner_id', 'amount_total', 'state', 'date_order'],
        limit=limite
    )

@mcp.tool()
@trazar
def consultar_facturas(limite: int = 10, estado: str = None) -> list:
    """
    Consulta las facturas de clientes registradas en Odoo.
    estado puede ser: 'draft' (borrador), 'posted' (confirmada), 'cancel' (cancelada)
    """
    if odoo is None:
        raise OdooNoDisponibleError("El servicio no se inicializó correctamente al arrancar")

    domain = [('move_type', '=', 'out_invoice')]
    if estado:
        domain.append(('state', '=', estado))

    return odoo.search_read(
        'account.move',
        domain,
        ['name', 'partner_id', 'amount_total', 'currency_id', 'state', 'invoice_date'],
        limit=limite
    )

@mcp.tool()
@trazar
def consultar_inventario(limite: int = 20) -> list:
    """Consulta el nivel de inventario (stock disponible) de los productos en Odoo."""
    if odoo is None:
        raise OdooNoDisponibleError("El servicio no se inicializó correctamente al arrancar")
    return odoo.search_read(
        'product.product',
        [('type', '=', 'product')],
        ['name', 'qty_available', 'virtual_available', 'default_code'],
        limit=limite
    )

@mcp.tool()
@trazar
def enviar_correo_cliente(destinatario: str, asunto: str, cuerpo: str) -> dict:
    """
    Envía un correo electrónico a un destinatario usando Gmail.
    Útil para enviar resúmenes de facturas, confirmaciones de pedidos o notificaciones a clientes.
    """
    resultado = enviar_correo(destinatario, asunto, cuerpo)
    return {
        "estado": "enviado",
        "id_mensaje": resultado.get("id"),
        "destinatario": destinatario
    }

@mcp.tool()
@trazar
def consultar_correos_recientes(cantidad: int = 5) -> list:
    """Consulta los correos más recientes de la bandeja de entrada de Gmail."""
    return consultar_correos(cantidad)


@mcp.tool()
@trazar
def consultar_correos_cliente(email_cliente: str = None, numero_factura: str = None, asunto_contiene: str = None, cantidad: int = 10) -> list:
    """
    Consulta correos electrónicos asociados a un cliente específico, a un número de factura/pedido,
    o que contengan cierto texto en el asunto. Debes proporcionar al menos uno de los tres parámetros.
    Útil para revisar la comunicación previa con un cliente antes de responderle o enviarle una factura.
    """
    partes_query = []
    if email_cliente:
        partes_query.append(f"(from:{email_cliente} OR to:{email_cliente})")
    if numero_factura:
        partes_query.append(f'"{numero_factura}"')
    if asunto_contiene:
        partes_query.append(f"subject:{asunto_contiene}")

    if not partes_query:
        raise ValueError("Debes indicar al menos un criterio: email_cliente, numero_factura o asunto_contiene")

    query = " ".join(partes_query)
    return consultar_correos_por_criterio(query, cantidad)

@mcp.tool()
@trazar
def consultar_trm(fecha: str = None) -> dict:
    """
    Consulta la Tasa Representativa del Mercado (TRM) de Colombia.
    Si no se especifica fecha, devuelve la TRM más reciente disponible.
    fecha en formato 'YYYY-MM-DD' (opcional).
    """
    if fecha:
        return consultar_trm_fecha(fecha)
    return consultar_trm_actual()

@mcp.tool()
@trazar
def convertir_moneda_a_cop(valor: float, moneda: str = "USD") -> dict:
    """
    Convierte un valor en moneda extranjera (por defecto USD) a pesos colombianos
    usando la TRM vigente del día.
    """
    return convertir_a_cop(valor, moneda)

@mcp.tool()
@trazar
def generar_reporte_clientes(formato: str = "pdf") -> str:
    """Genera un reporte de clientes en formato PDF o Excel. formato: 'pdf' o 'excel'."""
    if odoo is None:
        raise OdooNoDisponibleError("El servicio no se inicializó correctamente al arrancar")
    clientes = odoo.search_read('res.partner', [('customer_rank', '>', 0)], ['name', 'email', 'phone'])
    columnas = ['name', 'email', 'phone']
    if formato == "excel":
        ruta = generar_reporte_excel("Reporte de Clientes", clientes, columnas)
    else:
        ruta = generar_reporte_pdf("Reporte de Clientes", clientes, columnas)
    return f"Reporte generado en: {ruta}"


@mcp.tool()
@trazar
def generar_reporte_facturas(formato: str = "pdf") -> str:
    """Genera un reporte de facturas en formato PDF o Excel. formato: 'pdf' o 'excel'."""
    if odoo is None:
        raise OdooNoDisponibleError("El servicio no se inicializó correctamente al arrancar")
    facturas = odoo.search_read(
        'account.move',
        [('move_type', '=', 'out_invoice')],
        ['name', 'amount_total', 'state', 'invoice_date']
    )
    columnas = ['name', 'amount_total', 'state', 'invoice_date']
    if formato == "excel":
        ruta = generar_reporte_excel("Reporte de Facturas", facturas, columnas)
    else:
        ruta = generar_reporte_pdf("Reporte de Facturas", facturas, columnas)
    return f"Reporte generado en: {ruta}"

@mcp.tool()
def consultar_trazabilidad(limite: int = 10) -> list:
    """Consulta el historial de invocaciones MCP realizadas, con herramienta, parámetros, duración y estado."""
    return obtener_historial(limite)



if __name__ == "__main__":
    mcp.run(transport="streamable-http")