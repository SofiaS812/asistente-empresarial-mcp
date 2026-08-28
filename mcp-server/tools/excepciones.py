class ServicioNoDisponibleError(Exception):
    """Excepción base para cuando un servicio integrado no está disponible."""
    def __init__(self, servicio: str, detalle: str = ""):
        self.servicio = servicio
        self.detalle = detalle
        mensaje = f"El servicio '{servicio}' no está disponible en este momento."
        if detalle:
            mensaje += f" Detalle: {detalle}"
        super().__init__(mensaje)


class OdooNoDisponibleError(ServicioNoDisponibleError):
    def __init__(self, detalle: str = ""):
        super().__init__("Odoo (ERP)", detalle)


class GmailNoDisponibleError(ServicioNoDisponibleError):
    def __init__(self, detalle: str = ""):
        super().__init__("Gmail", detalle)


class TRMNoDisponibleError(ServicioNoDisponibleError):
    def __init__(self, detalle: str = ""):
        super().__init__("API de TRM", detalle)