import sqlite3
import os
import sys
from datetime import date
from tkinter import messagebox
from openpyxl import load_workbook

from constantes import DB_FILE, DATA_START, COLS


def db_connect():
    base = os.path.dirname(
        sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    )
    return sqlite3.connect(os.path.join(base, DB_FILE))


def db_inicializar():
    con = db_connect()
    con.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS planillas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id   INTEGER NOT NULL REFERENCES empleados(id),
            mes           INTEGER NOT NULL,
            anio          INTEGER NOT NULL,
            horas         TEXT DEFAULT '',
            hrs_extras    TEXT DEFAULT '',
            hrs_noct      TEXT DEFAULT '',
            adelanto      TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            origen        TEXT DEFAULT 'manual',
            UNIQUE(empleado_id, mes, anio)
        )
    """)
    try:
        con.execute("ALTER TABLE planillas ADD COLUMN origen TEXT DEFAULT 'manual'")
    except Exception:
        pass
    try:
        con.execute("ALTER TABLE planillas ADD COLUMN horas_base TEXT DEFAULT ''")
    except Exception:
        pass
    con.execute("""
        CREATE TABLE IF NOT EXISTS registro_diario (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER NOT NULL REFERENCES empleados(id),
            fecha       TEXT NOT NULL,
            horas       REAL DEFAULT 0,
            UNIQUE(empleado_id, fecha)
        )
    """)
    con.commit()
    con.close()


def db_importar_excel(path):
    con = db_connect()
    cur = con.cursor()
    if cur.execute("SELECT COUNT(*) FROM empleados").fetchone()[0] > 0:
        con.close()
        return
    wb = load_workbook(path)
    ws = wb.active
    hoy = date.today()
    for row in ws.iter_rows(min_row=DATA_START, values_only=True):
        nombre = row[0]
        if nombre is None:
            continue
        nombre = str(nombre).strip()
        cur.execute("INSERT OR IGNORE INTO empleados (nombre) VALUES (?)", (nombre,))
        emp_id = cur.execute(
            "SELECT id FROM empleados WHERE nombre=?", (nombre,)
        ).fetchone()[0]
        cur.execute(
            """
            INSERT OR IGNORE INTO planillas
                (empleado_id, mes, anio, horas, hrs_extras, hrs_noct, adelanto, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                emp_id,
                hoy.month,
                hoy.year,
                str(row[1]).strip() if row[1] is not None else "",
                str(row[2]).strip() if row[2] is not None else "",
                str(row[3]).strip() if row[3] is not None else "",
                str(row[4]).strip() if row[4] is not None else "",
                str(row[5]).strip() if row[5] is not None else "",
            ),
        )
    con.commit()
    con.close()


def db_asegurar_mes(mes, anio):
    con = db_connect()
    cur = con.cursor()
    empleados = cur.execute("SELECT id FROM empleados WHERE activo=1").fetchall()
    for (emp_id,) in empleados:
        cur.execute(
            """
            INSERT OR IGNORE INTO planillas
                (empleado_id, mes, anio, horas, hrs_extras, hrs_noct, adelanto, observaciones)
            VALUES (?, ?, ?, '', '', '', '', '')
        """,
            (emp_id, mes, anio),
        )
    con.commit()
    con.close()


def db_cargar_mes(mes, anio):
    db_asegurar_mes(mes, anio)
    con = db_connect()
    cur = con.cursor()
    rows = cur.execute(
        """
        SELECT e.nombre, p.horas, p.hrs_extras, p.hrs_noct, p.adelanto, p.observaciones, p.origen
        FROM planillas p
        JOIN empleados e ON e.id = p.empleado_id
        WHERE p.mes=? AND p.anio=? AND e.activo=1
        ORDER BY e.id
    """,
        (mes, anio),
    ).fetchall()
    con.close()
    return [
        {
            "Empleado": r[0],
            "Horas": r[1] or "",
            "Hrs. Extras": r[2] or "",
            "Hrs. Noct.": r[3] or "",
            "Adelanto": r[4] or "",
            "Observaciones": r[5] or "",
            "Origen": r[6] or "manual",
        }
        for r in rows
    ]


def db_guardar_fila(nombre, mes, anio, datos):
    con = db_connect()
    cur = con.cursor()
    emp = cur.execute("SELECT id FROM empleados WHERE nombre=?", (nombre,)).fetchone()
    if emp is None:
        con.close()
        return
    cur.execute(
        """
        UPDATE planillas SET
            horas=?, hrs_extras=?, hrs_noct=?, adelanto=?, observaciones=?,
            origen='manual', horas_base=''
        WHERE empleado_id=? AND mes=? AND anio=?
    """,
        (
            datos["Horas"],
            datos["Hrs. Extras"],
            datos["Hrs. Noct."],
            datos["Adelanto"],
            datos["Observaciones"],
            emp[0],
            mes,
            anio,
        ),
    )
    con.commit()
    con.close()


def db_agregar_empleado(nombre, mes, anio):
    con = db_connect()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO empleados (nombre) VALUES (?)", (nombre,))
        emp_id = cur.lastrowid
        meses_existentes = cur.execute(
            "SELECT DISTINCT mes, anio FROM planillas"
        ).fetchall()
        for m, a in meses_existentes:
            cur.execute(
                """
                INSERT OR IGNORE INTO planillas
                    (empleado_id, mes, anio, horas, hrs_extras, hrs_noct, adelanto, observaciones)
                VALUES (?, ?, ?, '', '', '', '', '')
            """,
                (emp_id, m, a),
            )
        cur.execute(
            """
            INSERT OR IGNORE INTO planillas
                (empleado_id, mes, anio, horas, hrs_extras, hrs_noct, adelanto, observaciones)
            VALUES (?, ?, ?, '', '', '', '', '')
        """,
            (emp_id, mes, anio),
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        messagebox.showwarning(
            "Duplicado", f"Ya existe un empleado llamado '{nombre}'."
        )
        return False
    finally:
        con.close()


def db_eliminar_empleado(nombre):
    con = db_connect()
    con.execute("UPDATE empleados SET activo=0 WHERE nombre=?", (nombre,))
    con.commit()
    con.close()


def db_cargar_empleados_activos():
    con = db_connect()
    rows = con.execute(
        "SELECT nombre FROM empleados WHERE activo=1 ORDER BY id"
    ).fetchall()
    con.close()
    return [r[0] for r in rows]


def db_cargar_registro_diario(nombre, mes, anio):
    con = db_connect()
    cur = con.cursor()
    emp = cur.execute("SELECT id FROM empleados WHERE nombre=?", (nombre,)).fetchone()
    if emp is None:
        con.close()
        return {}
    rows = cur.execute(
        """
        SELECT fecha, horas FROM registro_diario
        WHERE empleado_id=? AND strftime('%m', fecha)=? AND strftime('%Y', fecha)=?
    """,
        (emp[0], f"{mes:02d}", str(anio)),
    ).fetchall()
    con.close()
    return {r[0]: r[1] for r in rows}


def db_guardar_registro_dia(nombre, fecha_str, horas):
    con = db_connect()
    cur = con.cursor()
    emp = cur.execute("SELECT id FROM empleados WHERE nombre=?", (nombre,)).fetchone()
    if emp is None:
        con.close()
        return
    if horas == 0:
        cur.execute(
            "DELETE FROM registro_diario WHERE empleado_id=? AND fecha=?",
            (emp[0], fecha_str),
        )
    else:
        cur.execute(
            """
            INSERT INTO registro_diario (empleado_id, fecha, horas)
            VALUES (?, ?, ?)
            ON CONFLICT(empleado_id, fecha) DO UPDATE SET horas=excluded.horas
        """,
            (emp[0], fecha_str, horas),
        )
    con.commit()
    con.close()


def db_sincronizar_total_diario(nombre, mes, anio):
    """Suma horas_base + registro diario y escribe el total en horas."""
    con = db_connect()
    cur = con.cursor()
    emp = cur.execute("SELECT id FROM empleados WHERE nombre=?", (nombre,)).fetchone()
    if emp is None:
        con.close()
        return

    fila = cur.execute(
        "SELECT horas, origen, horas_base FROM planillas WHERE empleado_id=? AND mes=? AND anio=?",
        (emp[0], mes, anio),
    ).fetchone()

    horas_base = 0.0
    if fila:
        horas_actual, origen_actual, horas_base_guardada = fila
        if origen_actual == "manual" and horas_actual:
            try:
                horas_base = float(horas_actual.strip())
            except ValueError:
                horas_base = 0.0
            cur.execute(
                "UPDATE planillas SET horas_base=? WHERE empleado_id=? AND mes=? AND anio=?",
                (str(horas_base), emp[0], mes, anio),
            )
        elif horas_base_guardada:
            try:
                horas_base = float(horas_base_guardada)
            except ValueError:
                horas_base = 0.0

    registros = db_cargar_registro_diario(nombre, mes, anio)
    total_diario = sum(v for v in registros.values() if v > 0)
    total_final = horas_base + total_diario
    total_str = (
        str(int(total_final)) if total_final == int(total_final) else str(total_final)
    )

    cur.execute(
        "UPDATE planillas SET horas=?, origen='diario' WHERE empleado_id=? AND mes=? AND anio=?",
        (total_str if total_final > 0 else "", emp[0], mes, anio),
    )
    con.commit()
    con.close()
