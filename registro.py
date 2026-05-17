import customtkinter as ctk
import tkinter as tk
import calendar
from datetime import date

from constantes import (
    C_NAVY, C_BLUE, C_BLUE_FAINT, C_BLUE_LIGHT,
    C_GRAY100, C_GRAY200, C_GRAY400, C_GRAY600, C_GRAY800, C_RED,
    DIAS_SEMANA,
)
from db import (
    db_cargar_empleados_activos,
    db_cargar_registro_diario,
    db_guardar_registro_dia,
    db_sincronizar_total_diario,
    db_cargar_mes,
)


class FrameRegistro(ctk.CTkFrame):
    """Sección de registro de horas por día para cada empleado."""

    def __init__(self, parent, get_mes_anio, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.get_mes_anio    = get_mes_anio
        self.empleado_actual = tk.StringVar()
        self.celdas          = {}
        self.after_id        = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._construir()

    def _construir(self):
        # ── Selector de empleado ──────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="white", border_width=1, border_color=C_GRAY200)
        top.grid(row=0, column=0, padx=16, pady=(8, 6), sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="Empleado:", font=ctk.CTkFont(size=13), text_color=C_GRAY600
        ).grid(row=0, column=0, padx=(14, 8), pady=10)

        self.combo = ctk.CTkOptionMenu(
            top,
            variable=self.empleado_actual,
            values=[""],
            fg_color=C_BLUE_FAINT,
            button_color=C_BLUE,
            button_hover_color=C_NAVY,
            text_color=C_NAVY,
            font=ctk.CTkFont(size=13),
            command=lambda _: self._cargar_grilla(),
        )
        self.combo.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="w")

        ctk.CTkLabel(
            top,
            text="Hacé clic en una celda para editar · Enter o Tab para confirmar",
            font=ctk.CTkFont(size=11),
            text_color=C_GRAY400,
        ).grid(row=0, column=2, padx=(0, 14), pady=10, sticky="e")
        top.grid_columnconfigure(2, weight=1)

        # ── Área scrollable de la grilla ──────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="white", border_width=1, border_color=C_GRAY200
        )
        self.scroll.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=0)
        for c in range(1, 8):
            self.scroll.grid_columnconfigure(c, weight=1)

        # ── Barra de resumen ──────────────────────────────────────────
        resumen = ctk.CTkFrame(self, fg_color="white", border_width=1, border_color=C_GRAY200)
        resumen.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        for i in range(4):
            resumen.columnconfigure(i, weight=1)

        self.res_labels = {}
        for i, (key, titulo) in enumerate([
            ("dias",    "Días trabajados"),
            ("total",   "Total de horas"),
            ("promedio","Promedio / día"),
            ("extras",  "Horas extra est."),
        ]):
            ctk.CTkLabel(
                resumen, text=titulo, font=ctk.CTkFont(size=11), text_color=C_GRAY600
            ).grid(row=0, column=i, padx=12, pady=(10, 0), sticky="w")
            lbl = ctk.CTkLabel(
                resumen,
                text="—",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=C_NAVY if key != "extras" else C_BLUE,
            )
            lbl.grid(row=1, column=i, padx=12, pady=(0, 10), sticky="w")
            self.res_labels[key] = lbl

    # ── API pública ───────────────────────────────────────────────────
    def refrescar(self):
        empleados = db_cargar_empleados_activos()
        self.combo.configure(values=empleados if empleados else [""])
        if empleados:
            if self.empleado_actual.get() not in empleados:
                self.empleado_actual.set(empleados[0])
        else:
            self.empleado_actual.set("")
        self._cargar_grilla()

    # ── Grilla ───────────────────────────────────────────────────────
    def _cargar_grilla(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.celdas.clear()

        mes, anio = self.get_mes_anio()
        nombre    = self.empleado_actual.get()
        if not nombre:
            return

        hoy        = date.today()
        registros  = db_cargar_registro_diario(nombre, mes, anio)
        _, n_dias  = calendar.monthrange(anio, mes)
        primer_dia = date(anio, mes, 1).weekday()

        # Encabezados
        ctk.CTkLabel(
            self.scroll, text="#",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C_GRAY400, width=32, anchor="center",
        ).grid(row=0, column=0, padx=(4, 2), pady=(4, 2))

        for c, dia_nombre in enumerate(DIAS_SEMANA):
            color = C_RED if c >= 5 else C_GRAY600
            ctk.CTkLabel(
                self.scroll, text=dia_nombre,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color, anchor="center",
            ).grid(row=0, column=c + 1, padx=2, pady=(4, 2), sticky="ew")

        semana = 1
        col    = primer_dia
        dia    = 1

        ctk.CTkLabel(
            self.scroll, text=str(semana),
            font=ctk.CTkFont(size=11), text_color=C_GRAY400, width=32, anchor="center",
        ).grid(row=semana, column=0, padx=(4, 2), pady=2)

        for c in range(primer_dia):
            ctk.CTkLabel(self.scroll, text="", width=50).grid(
                row=semana, column=c + 1, padx=2, pady=2, sticky="ew"
            )

        while dia <= n_dias:
            fecha     = date(anio, mes, dia)
            fecha_str = fecha.isoformat()
            es_finde  = col >= 5
            es_hoy    = fecha == hoy
            val_actual = registros.get(fecha_str, 0)

            if es_finde:
                bg = C_GRAY100
            elif es_hoy:
                bg = C_BLUE_LIGHT
            else:
                bg = "white"

            celda_frame = ctk.CTkFrame(
                self.scroll, fg_color=bg,
                border_width=1, border_color=C_GRAY200, corner_radius=4,
            )
            celda_frame.grid(row=semana, column=col + 1, padx=2, pady=2, sticky="ew")
            celda_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                celda_frame, text=str(dia),
                font=ctk.CTkFont(size=9), text_color=C_GRAY400, anchor="e",
            ).grid(row=0, column=0, padx=4, pady=(3, 0), sticky="e")

            var = tk.StringVar(value=str(val_actual) if val_actual else "")
            entry = ctk.CTkEntry(
                celda_frame, textvariable=var,
                font=ctk.CTkFont(size=12), height=28,
                fg_color="transparent", border_width=0,
                justify="center", placeholder_text="—", text_color=C_GRAY800,
            )
            entry.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="ew")

            entry.bind("<FocusOut>", lambda e, fs=fecha_str, v=var: self._on_cambio(fs, v))
            entry.bind("<Return>",   lambda e, fs=fecha_str, v=var: self._on_cambio(fs, v))
            entry.bind("<Tab>",      lambda e, fs=fecha_str, v=var: self._on_cambio(fs, v))

            self.celdas[fecha_str] = var

            col += 1
            if col == 7:
                col     = 0
                semana += 1
                if dia < n_dias:
                    ctk.CTkLabel(
                        self.scroll, text=str(semana),
                        font=ctk.CTkFont(size=11), text_color=C_GRAY400,
                        width=32, anchor="center",
                    ).grid(row=semana, column=0, padx=(4, 2), pady=2)
            dia += 1

        self._actualizar_resumen(registros)

    def _on_cambio(self, fecha_str, var):
        nombre = self.empleado_actual.get()
        if not nombre:
            return
        txt = var.get().strip().replace(",", ".")
        try:
            horas = float(txt) if txt else 0.0
        except ValueError:
            horas = 0.0
            var.set("")
        db_guardar_registro_dia(nombre, fecha_str, horas)
        mes, anio = self.get_mes_anio()
        db_sincronizar_total_diario(nombre, mes, anio)
        registros = db_cargar_registro_diario(nombre, mes, anio)
        self._actualizar_resumen(registros)
        app = self.winfo_toplevel()
        app.empleados = db_cargar_mes(mes, anio)
        app._refrescar_stats()
        app._refrescar_tabla()

    def _actualizar_resumen(self, registros):
        valores = [v for v in registros.values() if v > 0]
        dias    = len(valores)
        total   = sum(valores)
        prom    = total / dias if dias else 0
        extras  = sum(max(0, v - 8) for v in valores)

        self.res_labels["dias"].configure(text=str(dias))
        self.res_labels["total"].configure(text=f"{total:.1f} hs")
        self.res_labels["promedio"].configure(text=f"{prom:.1f} hs")
        self.res_labels["extras"].configure(text=f"{extras:.1f} hs")
