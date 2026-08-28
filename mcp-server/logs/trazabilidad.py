import sqlite3
import time
import json
import os
from datetime import datetime
from functools import wraps

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "logs", "trazabilidad.db")


def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invocaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            herramienta TEXT NOT NULL,
            parametros TEXT,
            fecha_hora TEXT NOT NULL,
            duracion_ms REAL,
            estado TEXT,
            resultado_resumen TEXT,
            error TEXT
        )
    """)
    conn.commit()
    conn.close()


_init_db()


def registrar_invocacion(herramienta, parametros, duracion_ms, estado, resultado_resumen=None, error=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO invocaciones
           (herramienta, parametros, fecha_hora, duracion_ms, estado, resultado_resumen, error)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            herramienta,
            json.dumps(parametros, ensure_ascii=False, default=str),
            datetime.now().isoformat(),
            duracion_ms,
            estado,
            str(resultado_resumen)[:300] if resultado_resumen else None,
            str(error)[:300] if error else None
        )
    )
    conn.commit()
    conn.close()


def trazar(func):
    """Decorador que registra automáticamente cada invocación de una tool MCP."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.perf_counter()
        try:
            resultado = func(*args, **kwargs)
            duracion_ms = (time.perf_counter() - inicio) * 1000
            registrar_invocacion(
                herramienta=func.__name__,
                parametros=kwargs if kwargs else args,
                duracion_ms=duracion_ms,
                estado="exito",
                resultado_resumen=resultado
            )
            return resultado
        except Exception as e:
            duracion_ms = (time.perf_counter() - inicio) * 1000
            registrar_invocacion(
                herramienta=func.__name__,
                parametros=kwargs if kwargs else args,
                duracion_ms=duracion_ms,
                estado="error",
                error=str(e)
            )
            raise
    return wrapper


def obtener_historial(limite=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT * FROM invocaciones ORDER BY id DESC LIMIT ?", (limite,)
    )
    filas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return filas