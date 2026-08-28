import xmlrpc.client
import os
import time
from dotenv import load_dotenv
from tools.excepciones import OdooNoDisponibleError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class OdooClient:
    def __init__(self):
        self.url = os.getenv("ODOO_URL")
        self.db = os.getenv("ODOO_DB")
        self.username = os.getenv("ODOO_USER")
        self.password = os.getenv("ODOO_PASSWORD")

        try:
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        except (ConnectionRefusedError, OSError, TimeoutError) as e:
            raise OdooNoDisponibleError(f"No se pudo conectar a {self.url}. ¿Está corriendo el contenedor?") from e

        if not self.uid:
            raise OdooNoDisponibleError("Autenticación fallida. Revisa usuario/contraseña/BD en .env")

        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def search_read(self, model, domain=None, fields=None, limit=None):
        domain = domain or []
        fields = fields or []
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_read',
                [domain],
                {'fields': fields, 'limit': limit or 0}
            )
        except (ConnectionRefusedError, OSError, TimeoutError) as e:
            raise OdooNoDisponibleError(f"Error consultando {model}: {e}") from e

    def create(self, model, values):
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'create', [values]
            )
        except (ConnectionRefusedError, OSError, TimeoutError) as e:
            raise OdooNoDisponibleError(f"Error creando registro en {model}: {e}") from e


def _conectar_con_reintentos(intentos=10, espera_segundos=3):
    for intento in range(1, intentos + 1):
        try:
            cliente = OdooClient()
            print(f"[Odoo] Conexión exitosa en el intento {intento}")
            return cliente
        except OdooNoDisponibleError as e:
            print(f"[Odoo] Intento {intento}/{intentos} falló: {e}. Reintentando en {espera_segundos}s...")
            time.sleep(espera_segundos)
    print("[Odoo] No se pudo conectar tras varios intentos. El servicio quedará como no disponible.")
    return None

odoo = _conectar_con_reintentos()