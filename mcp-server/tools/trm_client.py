import requests
from datetime import datetime
from tools.excepciones import TRMNoDisponibleError

TRM_API_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"


def consultar_trm_actual() -> dict:
    """Consulta la TRM más reciente disponible."""
    try:
        params = {"$order": "vigenciadesde DESC", "$limit": 1}
        respuesta = requests.get(TRM_API_URL, params=params, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except requests.exceptions.RequestException as e:
        raise TRMNoDisponibleError(f"No se pudo conectar a la API de TRM: {e}") from e

    if not datos:
        raise TRMNoDisponibleError("La API respondió pero sin datos de TRM")

    registro = datos[0]
    return {
        "valor": float(registro["valor"]),
        "vigencia_desde": registro["vigenciadesde"],
        "unidad": registro.get("unidad", "COP")
    }


def consultar_trm_fecha(fecha: str) -> dict:
    """
    Consulta la TRM vigente para una fecha específica.
    fecha en formato 'YYYY-MM-DD'
    """
    try:
     params = {"$where": f"vigenciadesde <= '{fecha}T00:00:00.000' AND vigenciahasta >= '{fecha}T00:00:00.000'", "$limit": 1}
     respuesta = requests.get(TRM_API_URL, params=params, timeout=10)
     respuesta.raise_for_status()
     datos = respuesta.json()
    except requests.exceptions.RequestException as e:
     raise TRMNoDisponibleError(f"No se pudo conectar a la API de TRM: {e}") from e


    if not datos:
        return consultar_trm_actual()

    registro = datos[0]
    return {
        "valor": float(registro["valor"]),
        "vigencia_desde": registro["vigenciadesde"],
        "unidad": registro.get("unidad", "COP")
    }


def convertir_a_cop(valor_extranjero: float, moneda_origen: str = "USD") -> dict:
    """Convierte un valor en moneda extranjera a pesos colombianos usando la TRM actual."""
    trm = consultar_trm_actual()
    valor_cop = valor_extranjero * trm["valor"]

    return {
        "valor_original": valor_extranjero,
        "moneda_original": moneda_origen,
        "trm_aplicada": trm["valor"],
        "valor_convertido_cop": round(valor_cop, 2),
        "fecha_trm": trm["vigencia_desde"]
    }