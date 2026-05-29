import customtkinter as ctk
import tkinter as tk
import calendar
from datetime import date

from constantes import (
    C_NAVY,
    C_BLUE,
    C_BLUE_FAINT,
    C_BLUE_LIGHT,
    C_BLUE_MID,
    C_GRAY100,
    C_GRAY200,
    C_GRAY400,
    C_GRAY600,
    C_GRAY800,
    C_RED,
    C_GREEN,
    DIAS_SEMANA,
)


def decimal_a_tiempo(n):
    """Convierte 7.75 en '7:45'"""
    if not n or n <= 0:
        return ""
    horas = int(n)
    minutos = int(round((n - horas) * 60))
    if minutos == 0:
        return f"{horas}:00"
    return f"{horas}:{minutos:02d}"


def tiempo_a_decimal(cadena):
    cadena = cadena.replace(",", ".").strip()
    if ":" in cadena:
        partes = cadena.split(":")
        h = float(partes[0]) if partes[0] else 0.0
        m = float(partes[1]) if len(partes) > 1 and partes[1] else 0.0
        return h + (m / 60)
    return float(cadena) if cadena else 0.0


def parse_horas(txt):
    txt = txt.lower().strip()
    if not txt:
        return 0.0
    txt = txt.replace(" y ", " ").replace("+", " ").replace(";", " ")
    bloques = txt.split()
    total_horas = 0.0
    for bloque in bloques:
        bloque = bloque.strip(",")
        if "-" in bloque:
            partes = bloque.split("-")
            if len(partes) == 2:
                try:
                    inicio = tiempo_a_decimal(partes[0])
                    fin = tiempo_a_decimal(partes[1])
                    total_horas += max(0.0, fin - inicio)
                except ValueError:
                    continue
        else:
            try:
                total_horas += tiempo_a_decimal(bloque)
            except ValueError:
                continue
    return round(total_horas, 2)


# ── Time Picker Popup ─────────────────────────────────────────────────


class TimePickerPopup(tk.Toplevel):
    """
    Popup visual para seleccionar horas. Soporta hasta 3 bloques horarios
    (jornada partida) y modo cantidad directa.
    """

    MINUTOS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

    # Cada bloque: (hora_entrada, min_entrada, hora_salida, min_salida, activo)
    MAX_BLOQUES = 3

    def __init__(self, parent, on_confirm, valor_actual=None, x=None, y=None):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.modo = tk.StringVar(value="rango")

        # Variables para cada bloque
        self.bloques = []
        defaults = [(8, 0, 12, 0), (13, 0, 17, 0), (18, 0, 20, 0)]
        for he, me, hs, ms in defaults:
            self.bloques.append(
                {
                    "hora_entrada": tk.IntVar(value=he),
                    "min_entrada": tk.IntVar(value=me),
                    "hora_salida": tk.IntVar(value=hs),
                    "min_salida": tk.IntVar(value=ms),
                    "activo": tk.BooleanVar(value=False),
                }
            )
        self.bloques[0]["activo"].set(True)  # primer bloque siempre activo

        self.cantidad = tk.DoubleVar(value=8.0)

        if valor_actual:
            self._prellenar(valor_actual)

        self._build_ui()
        self._actualizar_preview()

        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = parent.winfo_screenwidth()
        sh = parent.winfo_screenheight()
        px = (x or sw // 2) - w // 2
        py = (y or sh // 2) + 10
        if px + w > sw - 10:
            px = sw - w - 10
        if py + h > sh - 40:
            py = (y or sh // 2) - h - 10
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.focus_force()

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def _prellenar(self, valor_actual):
        try:
            txt = str(valor_actual).strip()
            if not txt or txt in ("0", "0:00", "—", ""):
                return
            if "-" in txt:
                partes = txt.split("-")
                if len(partes) == 2:
                    ini = tiempo_a_decimal(partes[0])
                    fin = tiempo_a_decimal(partes[1])
                    self.bloques[0]["hora_entrada"].set(int(ini))
                    self.bloques[0]["min_entrada"].set(round((ini - int(ini)) * 60))
                    self.bloques[0]["hora_salida"].set(int(fin))
                    self.bloques[0]["min_salida"].set(round((fin - int(fin)) * 60))
                    self.modo.set("rango")
            else:
                dec = tiempo_a_decimal(txt)
                if dec > 0:
                    self.cantidad.set(dec)
                    self.modo.set("cantidad")
        except Exception:
            pass

    def _build_ui(self):
        FONT_TITLE = ("Segoe UI", 12, "bold")
        FONT_SMALL = ("Segoe UI", 9)
        FONT_BTN = ("Segoe UI", 10, "bold")
        BG = "#FFFFFF"
        BG_CARD = "#F4F8FF"

        self.configure(bg=BG)

        outer = tk.Frame(self, bg=C_GRAY200, bd=0)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=BG, bd=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Encabezado
        header = tk.Frame(inner, bg=C_NAVY)
        header.pack(fill="x")
        title_lbl = tk.Label(
            header,
            text="⏰  Seleccionar horas",
            font=FONT_TITLE,
            bg=C_NAVY,
            fg="white",
            padx=14,
            pady=8,
            cursor="fleur",
        )
        title_lbl.pack(side="left")
        title_lbl.bind("<ButtonPress-1>", self._drag_start)
        title_lbl.bind("<B1-Motion>", self._drag_move)
        header.bind("<ButtonPress-1>", self._drag_start)
        header.bind("<B1-Motion>", self._drag_move)
        tk.Button(
            header,
            text="✕",
            font=("Segoe UI", 11),
            bg=C_NAVY,
            fg=C_GRAY400,
            relief="flat",
            activebackground=C_BLUE,
            activeforeground="white",
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.destroy,
        ).pack(side="right")

        # Selector de modo
        modo_frame = tk.Frame(inner, bg=BG, pady=8)
        modo_frame.pack(fill="x", padx=14)
        self._btn_rango = tk.Button(
            modo_frame,
            text="Entrada / Salida",
            font=FONT_SMALL,
            relief="flat",
            cursor="hand2",
            command=lambda: self._set_modo("rango"),
        )
        self._btn_cantidad = tk.Button(
            modo_frame,
            text="Cantidad de horas",
            font=FONT_SMALL,
            relief="flat",
            cursor="hand2",
            command=lambda: self._set_modo("cantidad"),
        )
        self._btn_rango.pack(side="left", padx=(0, 4))
        self._btn_cantidad.pack(side="left")
        self._actualizar_modo_botones()

        tk.Frame(inner, bg=C_GRAY200, height=1).pack(fill="x")

        # Contenido dinámico
        self._content = tk.Frame(inner, bg=BG)
        self._content.pack(fill="both", expand=True, padx=14, pady=10)

        self._build_panel_rango()
        self._build_panel_cantidad()
        self._mostrar_panel()

        tk.Frame(inner, bg=C_GRAY200, height=1).pack(fill="x")

        # Preview + botones
        bottom = tk.Frame(inner, bg=BG_CARD)
        bottom.pack(fill="x")

        self._preview_lbl = tk.Label(
            bottom, text="", font=("Segoe UI", 13, "bold"), bg=BG_CARD, fg=C_NAVY
        )
        self._preview_lbl.pack(side="left", padx=16, pady=10)

        btn_frame = tk.Frame(bottom, bg=BG_CARD)
        btn_frame.pack(side="right", padx=10, pady=8)

        tk.Button(
            btn_frame,
            text="Cancelar",
            font=FONT_BTN,
            bg=C_GRAY200,
            fg=C_NAVY,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            activebackground=C_GRAY400,
            command=self.destroy,
        ).pack(side="left", padx=(0, 6))

        self._btn_confirmar = tk.Button(
            btn_frame,
            text="✔  Confirmar",
            font=FONT_BTN,
            bg=C_BLUE,
            fg="white",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            activebackground=C_NAVY,
            activeforeground="white",
            command=self._confirmar,
        )
        self._btn_confirmar.pack(side="left")

    # ── Panel Rango ───────────────────────────────────────────────────

    def _build_panel_rango(self):
        self._panel_rango = tk.Frame(self._content, bg="white")

        # Contenedor de bloques (se reconstruye al activar/desactivar)
        self._bloques_container = tk.Frame(self._panel_rango, bg="white")
        self._bloques_container.pack(fill="x")

        # Botones para agregar bloques
        self._btns_agregar_frame = tk.Frame(self._panel_rango, bg="white")
        self._btns_agregar_frame.pack(fill="x", pady=(6, 0))

        self._rebuild_bloques()

    def _rebuild_bloques(self):
        """Reconstruye la UI de bloques según cuáles están activos."""
        for w in self._bloques_container.winfo_children():
            w.destroy()
        for w in self._btns_agregar_frame.winfo_children():
            w.destroy()

        bloques_activos = [b for b in self.bloques if b["activo"].get()]
        n_activos = len(bloques_activos)

        FONT_LBL = ("Segoe UI", 9)
        FONT_TIME = ("Segoe UI", 16, "bold")

        for i, bloque in enumerate(bloques_activos):
            fila = tk.Frame(self._bloques_container, bg="white")
            fila.pack(fill="x", pady=(0, 6))

            # Etiqueta del bloque
            lbl_texto = "Turno 1" if i == 0 else f"Turno {i + 1}"
            tk.Label(
                fila,
                text=lbl_texto,
                font=("Segoe UI", 9, "bold"),
                bg="white",
                fg=C_NAVY,
                width=7,
                anchor="w",
            ).pack(side="left", padx=(0, 6))

            # Selectores entrada/salida
            for lado, hora_var, min_var in [
                ("Entrada", bloque["hora_entrada"], bloque["min_entrada"]),
                ("Salida", bloque["hora_salida"], bloque["min_salida"]),
            ]:
                tk.Label(fila, text=lado, font=FONT_LBL, bg="white", fg=C_GRAY600).pack(
                    side="left", padx=(4, 2)
                )

                h_frame = tk.Frame(fila, bg="white")
                h_frame.pack(side="left")
                tk.Button(
                    h_frame,
                    text="▲",
                    font=("Segoe UI", 7),
                    relief="flat",
                    bg=C_BLUE_FAINT,
                    fg=C_NAVY,
                    cursor="hand2",
                    command=lambda v=hora_var: self._step_y_preview(v, 1, 0, 24),
                ).pack(fill="x")
                tk.Label(
                    h_frame,
                    textvariable=hora_var,
                    font=FONT_TIME,
                    bg="white",
                    fg=C_NAVY,
                    width=2,
                    anchor="center",
                ).pack()
                tk.Button(
                    h_frame,
                    text="▼",
                    font=("Segoe UI", 7),
                    relief="flat",
                    bg=C_BLUE_FAINT,
                    fg=C_NAVY,
                    cursor="hand2",
                    command=lambda v=hora_var: self._step_y_preview(v, -1, 0, 24),
                ).pack(fill="x")

                tk.Label(fila, text=":", font=FONT_TIME, bg="white", fg=C_NAVY).pack(
                    side="left"
                )

                m_frame = tk.Frame(fila, bg="white")
                m_frame.pack(side="left", padx=(0, 6))
                tk.Button(
                    m_frame,
                    text="▲",
                    font=("Segoe UI", 7),
                    relief="flat",
                    bg=C_BLUE_FAINT,
                    fg=C_NAVY,
                    cursor="hand2",
                    command=lambda v=min_var: self._step_min_y_preview(v, 1),
                ).pack(fill="x")
                tk.Label(
                    m_frame,
                    textvariable=min_var,
                    font=FONT_TIME,
                    bg="white",
                    fg=C_NAVY,
                    width=3,
                    anchor="center",
                ).pack()
                tk.Button(
                    m_frame,
                    text="▼",
                    font=("Segoe UI", 7),
                    relief="flat",
                    bg=C_BLUE_FAINT,
                    fg=C_NAVY,
                    cursor="hand2",
                    command=lambda v=min_var: self._step_min_y_preview(v, -1),
                ).pack(fill="x")

            # Botón quitar (solo en bloques extra)
            if i > 0:
                idx_real = self.bloques.index(bloque)
                tk.Button(
                    fila,
                    text="✕",
                    font=("Segoe UI", 9),
                    relief="flat",
                    bg="#FEE2E2",
                    fg=C_RED,
                    cursor="hand2",
                    padx=6,
                    pady=2,
                    command=lambda b=bloque: self._quitar_bloque(b),
                ).pack(side="left", padx=(4, 0))

        # Botones para agregar más bloques
        if n_activos < self.MAX_BLOQUES:
            etiqueta = "＋ Jornada partida" if n_activos == 1 else "＋ Agregar turno"
            tk.Button(
                self._btns_agregar_frame,
                text=etiqueta,
                font=("Segoe UI", 9),
                relief="flat",
                bg=C_BLUE_FAINT,
                fg=C_NAVY,
                cursor="hand2",
                padx=10,
                pady=4,
                command=self._agregar_bloque,
            ).pack(side="left", padx=(0, 4))

        # Accesos rápidos (solo cuando hay un bloque)
        if n_activos == 1:
            quick_frame = tk.Frame(self._panel_rango, bg="white")
            quick_frame.pack(fill="x", pady=(4, 0))
            tk.Label(
                quick_frame,
                text="Rápido:",
                font=("Segoe UI", 9),
                bg="white",
                fg=C_GRAY400,
            ).pack(side="left", padx=(0, 6))
            for texto, he, me, hs, ms in [
                ("8h", 8, 0, 16, 0),
                ("8:30h", 8, 30, 17, 0),
                ("9h", 9, 0, 18, 0),
                ("12h", 8, 0, 20, 0),
            ]:
                tk.Button(
                    quick_frame,
                    text=texto,
                    font=("Segoe UI", 9),
                    relief="flat",
                    bg=C_BLUE_FAINT,
                    fg=C_NAVY,
                    cursor="hand2",
                    padx=8,
                    pady=3,
                    command=lambda he=he, me=me, hs=hs, ms=ms: self._quick_rango(
                        he, me, hs, ms
                    ),
                ).pack(side="left", padx=2)

        self._actualizar_preview()

    def _agregar_bloque(self):
        for b in self.bloques:
            if not b["activo"].get():
                b["activo"].set(True)
                break
        self._rebuild_bloques()

    def _quitar_bloque(self, bloque):
        bloque["activo"].set(False)
        self._rebuild_bloques()

    # ── Panel Cantidad ────────────────────────────────────────────────

    def _build_panel_cantidad(self):
        FONT_BIG = ("Segoe UI", 22, "bold")
        FONT_LBL = ("Segoe UI", 10)

        self._panel_cantidad = tk.Frame(self._content, bg="white")

        tk.Label(
            self._panel_cantidad,
            text="Horas trabajadas",
            font=FONT_LBL,
            bg="white",
            fg=C_GRAY600,
        ).pack(pady=(0, 6))

        ctrl = tk.Frame(self._panel_cantidad, bg="white")
        ctrl.pack()

        tk.Button(
            ctrl,
            text="−",
            font=("Segoe UI", 16, "bold"),
            relief="flat",
            bg=C_BLUE_FAINT,
            fg=C_NAVY,
            width=3,
            cursor="hand2",
            command=lambda: self._step_cantidad(-0.5),
        ).pack(side="left", padx=4)

        tk.Label(
            ctrl,
            textvariable=self.cantidad,
            font=FONT_BIG,
            bg="white",
            fg=C_NAVY,
            width=5,
        ).pack(side="left")

        tk.Button(
            ctrl,
            text="+",
            font=("Segoe UI", 16, "bold"),
            relief="flat",
            bg=C_BLUE_FAINT,
            fg=C_NAVY,
            width=3,
            cursor="hand2",
            command=lambda: self._step_cantidad(0.5),
        ).pack(side="left", padx=4)

        quick_frame = tk.Frame(self._panel_cantidad, bg="white")
        quick_frame.pack(pady=(10, 0))
        tk.Label(
            quick_frame, text="Rápido:", font=("Segoe UI", 9), bg="white", fg=C_GRAY400
        ).pack(side="left", padx=(0, 6))
        for hs in [4, 6, 8, 9, 10, 12]:
            tk.Button(
                quick_frame,
                text=f"{hs}h",
                font=("Segoe UI", 9),
                relief="flat",
                bg=C_BLUE_FAINT,
                fg=C_NAVY,
                cursor="hand2",
                padx=8,
                pady=3,
                command=lambda h=hs: self._set_cantidad(h),
            ).pack(side="left", padx=2)

        self.cantidad.trace_add("write", lambda *a: self._actualizar_preview())

    # ── Helpers ───────────────────────────────────────────────────────

    def _set_modo(self, modo):
        self.modo.set(modo)
        self._actualizar_modo_botones()
        self._mostrar_panel()
        self._actualizar_preview()

    def _actualizar_modo_botones(self):
        modo = self.modo.get()
        for btn, key in [(self._btn_rango, "rango"), (self._btn_cantidad, "cantidad")]:
            activo = modo == key
            btn.configure(
                bg=C_BLUE if activo else C_BLUE_FAINT,
                fg="white" if activo else C_NAVY,
                relief="flat",
                padx=12,
                pady=5,
            )

    def _mostrar_panel(self):
        self._panel_rango.pack_forget()
        self._panel_cantidad.pack_forget()
        if self.modo.get() == "rango":
            self._panel_rango.pack(fill="both", expand=True)
        else:
            self._panel_cantidad.pack(fill="both", expand=True)

    def _step_y_preview(self, var, delta, minv, maxv):
        var.set(max(minv, min(maxv, var.get() + delta)))
        self._actualizar_preview()

    def _step_min_y_preview(self, var, delta):
        idx = self.MINUTOS.index(var.get()) if var.get() in self.MINUTOS else 0
        var.set(self.MINUTOS[(idx + delta) % len(self.MINUTOS)])
        self._actualizar_preview()

    def _step_cantidad(self, delta):
        self.cantidad.set(round(max(0.0, min(24.0, self.cantidad.get() + delta)), 2))

    def _set_cantidad(self, val):
        self.cantidad.set(float(val))

    def _quick_rango(self, he, me, hs, ms):
        b = self.bloques[0]
        b["hora_entrada"].set(he)
        b["min_entrada"].set(me)
        b["hora_salida"].set(hs)
        b["min_salida"].set(ms)
        self._actualizar_preview()

    def _bloques_activos_decimales(self):
        """
        Devuelve lista de (entrada, salida) en decimal para cada bloque activo.
        Si salida < entrada se asume turno nocturno y se suma 24 a la salida.
        """
        resultado = []
        for b in self.bloques:
            if b["activo"].get():
                entrada = b["hora_entrada"].get() + b["min_entrada"].get() / 60
                salida = b["hora_salida"].get() + b["min_salida"].get() / 60
                if salida < entrada:  # turno nocturno
                    salida += 24
                resultado.append((entrada, salida))
        return resultado

    def _error_solapamiento(self):
        """
        Devuelve un mensaje de error si algún turno empieza antes de que
        termine el anterior, o None si todo está bien.
        """
        bloques = self._bloques_activos_decimales()
        for i in range(1, len(bloques)):
            fin_anterior = bloques[i - 1][1]
            inicio_actual = bloques[i][0]
            # Ajustamos inicio_actual si es turno nocturno que ya pasó medianoche
            if inicio_actual < bloques[i - 1][0]:
                inicio_actual += 24
            if inicio_actual < fin_anterior:
                return f"El Turno {i + 1} empieza antes de que termine el Turno {i}"
        return None

    def _calcular_horas(self):
        if self.modo.get() == "rango":
            total = sum(s - e for e, s in self._bloques_activos_decimales())
            return round(total, 4)
        else:
            return round(self.cantidad.get(), 2)

    def _actualizar_preview(self):
        if not hasattr(self, "_preview_lbl"):
            return

        if self.modo.get() == "rango":
            error = self._error_solapamiento()
            bloques_activos = [b for b in self.bloques if b["activo"].get()]
            partes = []
            for b in bloques_activos:
                he = b["hora_entrada"].get()
                me = b["min_entrada"].get()
                hs = b["hora_salida"].get()
                ms = b["min_salida"].get()
                partes.append(f"{he}:{me:02d}–{hs}:{ms:02d}")

            if error:
                self._preview_lbl.configure(
                    text=f"⚠  {error}",
                    font=("Segoe UI", 10, "bold"),
                    fg="#DC2626",
                )
                self._btn_confirmar.configure(
                    state="disabled", bg=C_GRAY200, fg=C_GRAY400
                )
            else:
                horas = self._calcular_horas()
                texto_total = decimal_a_tiempo(horas) if horas > 0 else "0:00"
                resumen = "  +  ".join(partes) + f"  =  {texto_total} hs"
                self._preview_lbl.configure(
                    text=resumen,
                    font=("Segoe UI", 13, "bold"),
                    fg=C_NAVY,
                )
                self._btn_confirmar.configure(state="normal", bg=C_BLUE, fg="white")
        else:
            horas = self._calcular_horas()
            texto_total = decimal_a_tiempo(horas) if horas > 0 else "0:00"
            self._preview_lbl.configure(
                text=f"{texto_total} hs",
                font=("Segoe UI", 22, "bold"),
                fg=C_NAVY,
            )
            self._btn_confirmar.configure(state="normal", bg=C_BLUE, fg="white")

    def _confirmar(self):
        if self.modo.get() == "rango" and self._error_solapamiento():
            return
        horas = self._calcular_horas()
        self.destroy()
        self.on_confirm(horas)


# ── Frame principal ───────────────────────────────────────────────────

from db import (
    db_cargar_empleados_activos,
    db_cargar_registro_diario,
    db_guardar_registro_dia,
    db_sincronizar_total_diario,
    db_cargar_mes,
)


class FrameRegistro(ctk.CTkFrame):
    """Sección de registro de horas por día para cada empleado."""

    TIPOS_REGISTRO = [
        ("Horas diarias", "horas"),
        ("Hrs. Extras", "hrs_extras"),
        ("Hrs. Nocturnas", "hrs_noct"),
    ]

    def __init__(self, parent, get_mes_anio, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.get_mes_anio = get_mes_anio
        self.empleado_actual = tk.StringVar()
        self.tipo_actual = tk.StringVar(value="Horas diarias")
        self.celdas = {}
        self.after_id = None
        self._popup_activo = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self._construir()

    def _construir(self):
        top = ctk.CTkFrame(
            self, fg_color="white", border_width=1, border_color=C_GRAY200
        )
        top.grid(row=0, column=0, padx=16, pady=(8, 6), sticky="ew")
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(2, weight=1)

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
            text="Hacé clic en una celda para seleccionar las horas",
            font=ctk.CTkFont(size=11),
            text_color=C_GRAY400,
        ).grid(row=0, column=2, padx=(0, 14), pady=10, sticky="e")

        self.tipo_frame = ctk.CTkFrame(
            self, fg_color="white", border_width=1, border_color=C_GRAY200
        )
        self.tipo_frame.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="ew")
        for i in range(len(self.TIPOS_REGISTRO)):
            self.tipo_frame.columnconfigure(i, weight=1)

        self.tipo_buttons = {}
        for i, (etiqueta, _) in enumerate(self.TIPOS_REGISTRO):
            btn = ctk.CTkButton(
                self.tipo_frame,
                text=etiqueta,
                font=ctk.CTkFont(size=12),
                fg_color=C_BLUE_FAINT,
                text_color=C_NAVY,
                hover_color=C_BLUE,
                command=lambda tipo=etiqueta: self._seleccionar_tipo(tipo),
            )
            left_pad = 8 if i == 0 else 4
            right_pad = 8 if i == len(self.TIPOS_REGISTRO) - 1 else 4
            btn.grid(row=0, column=i, padx=(left_pad, right_pad), pady=8, sticky="nsew")
            self.tipo_buttons[etiqueta] = btn
        self._actualizar_tipo_botones()

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="white", border_width=1, border_color=C_GRAY200
        )
        self.scroll.grid(row=2, column=0, padx=16, pady=(0, 6), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=0)
        for c in range(1, 8):
            self.scroll.grid_columnconfigure(c, weight=1)

        resumen = ctk.CTkFrame(
            self, fg_color="white", border_width=1, border_color=C_GRAY200
        )
        resumen.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")
        for i in range(5):
            resumen.columnconfigure(i, weight=1)

        self.res_labels = {}
        self.res_title_labels = {}
        for i, (key, titulo) in enumerate(
            [
                ("dias", "Días trabajados"),
                ("total", "Total de horas"),
                ("promedio", "Promedio / día"),
                ("extras", "Horas extras"),
                ("nocturnas", "Horas nocturnas"),
            ]
        ):
            title_lbl = ctk.CTkLabel(
                resumen, text=titulo, font=ctk.CTkFont(size=11), text_color=C_GRAY600
            )
            title_lbl.grid(row=0, column=i, padx=12, pady=(10, 0), sticky="w")
            lbl = ctk.CTkLabel(
                resumen,
                text="—",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=C_NAVY if key not in ("extras", "nocturnas") else C_BLUE,
            )
            lbl.grid(row=1, column=i, padx=12, pady=(0, 10), sticky="w")
            self.res_title_labels[key] = title_lbl
            self.res_labels[key] = lbl

    def refrescar(self):
        empleados = db_cargar_empleados_activos()
        self.combo.configure(values=empleados if empleados else [""])
        if empleados:
            if self.empleado_actual.get() not in empleados:
                self.empleado_actual.set(empleados[0])
        else:
            self.empleado_actual.set("")
        self._cargar_grilla()

    def _cargar_grilla(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.celdas.clear()

        mes, anio = self.get_mes_anio()
        nombre = self.empleado_actual.get()
        if not nombre:
            return

        hoy = date.today()
        registros = db_cargar_registro_diario(nombre, mes, anio, self._tipo_columna())
        _, n_dias = calendar.monthrange(anio, mes)
        primer_dia = date(anio, mes, 1).weekday()

        ctk.CTkLabel(
            self.scroll,
            text="#",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C_GRAY400,
            width=32,
            anchor="center",
        ).grid(row=0, column=0, padx=(4, 2), pady=(4, 2))

        for c, dia_nombre in enumerate(DIAS_SEMANA):
            color = C_RED if c >= 5 else C_GRAY600
            ctk.CTkLabel(
                self.scroll,
                text=dia_nombre,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color,
                anchor="center",
            ).grid(row=0, column=c + 1, padx=2, pady=(4, 2), sticky="ew")

        semana = 1
        col = primer_dia
        dia = 1

        ctk.CTkLabel(
            self.scroll,
            text=str(semana),
            font=ctk.CTkFont(size=11),
            text_color=C_GRAY400,
            width=32,
            anchor="center",
        ).grid(row=semana, column=0, padx=(4, 2), pady=2)

        for c in range(primer_dia):
            ctk.CTkLabel(self.scroll, text="", width=50).grid(
                row=semana, column=c + 1, padx=2, pady=2, sticky="ew"
            )

        while dia <= n_dias:
            fecha = date(anio, mes, dia)
            fecha_str = fecha.isoformat()
            es_finde = col >= 5
            es_hoy = fecha == hoy
            val_actual = registros.get(fecha_str, 0)

            bg = C_GRAY100 if es_finde else (C_BLUE_LIGHT if es_hoy else "white")

            celda_frame = ctk.CTkFrame(
                self.scroll,
                fg_color=bg,
                border_width=1,
                border_color=C_GRAY200,
                corner_radius=4,
                cursor="hand2",
            )
            celda_frame.grid(row=semana, column=col + 1, padx=2, pady=2, sticky="ew")
            celda_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                celda_frame,
                text=str(dia),
                font=ctk.CTkFont(size=9),
                text_color=C_GRAY400,
                anchor="e",
                cursor="hand2",
            ).grid(row=0, column=0, padx=4, pady=(3, 0), sticky="e")

            texto_horas = decimal_a_tiempo(val_actual) if val_actual else ""
            var = tk.StringVar(value=texto_horas)

            lbl_hora = ctk.CTkLabel(
                celda_frame,
                textvariable=var,
                font=ctk.CTkFont(size=12),
                text_color=C_NAVY if val_actual else C_GRAY400,
                anchor="center",
                height=28,
                cursor="hand2",
            )
            lbl_hora.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="ew")

            for widget in (celda_frame, lbl_hora):
                widget.bind(
                    "<Button-1>",
                    lambda e, fs=fecha_str, v=var, va=val_actual, cf=celda_frame: (
                        self._abrir_picker(e, fs, v, va, cf)
                    ),
                )

            self.celdas[fecha_str] = var

            col += 1
            if col == 7:
                col = 0
                semana += 1
                if dia < n_dias:
                    ctk.CTkLabel(
                        self.scroll,
                        text=str(semana),
                        font=ctk.CTkFont(size=11),
                        text_color=C_GRAY400,
                        width=32,
                        anchor="center",
                    ).grid(row=semana, column=0, padx=(4, 2), pady=2)
            dia += 1

        self._actualizar_resumen()

    def _abrir_picker(self, event, fecha_str, var, val_actual, celda_frame):
        if self._popup_activo and self._popup_activo.winfo_exists():
            self._popup_activo.destroy()

        try:
            cx = celda_frame.winfo_rootx()
            cy = celda_frame.winfo_rooty() + celda_frame.winfo_height()
        except Exception:
            cx, cy = None, None

        valor_previo = decimal_a_tiempo(val_actual) if val_actual else ""

        def on_confirm(horas):
            self._guardar_horas(fecha_str, var, horas)

        popup = TimePickerPopup(
            self.winfo_toplevel(),
            on_confirm=on_confirm,
            valor_actual=valor_previo,
            x=cx,
            y=cy,
        )
        self._popup_activo = popup

    def _guardar_horas(self, fecha_str, var, horas):
        nombre = self.empleado_actual.get()
        if not nombre:
            return
        tipo = self._tipo_columna()
        horas_guardadas = self._guardar_horas_y_split(nombre, fecha_str, tipo, horas)
        var.set(decimal_a_tiempo(horas_guardadas) if horas_guardadas > 0 else "")
        mes, anio = self.get_mes_anio()
        db_sincronizar_total_diario(nombre, mes, anio)
        self._actualizar_resumen()
        app = self.winfo_toplevel()
        app.empleados = db_cargar_mes(mes, anio)
        app._refrescar_stats()
        app._refrescar_tabla()

    def _seleccionar_tipo(self, tipo):
        if self.tipo_actual.get() == tipo:
            return
        self.tipo_actual.set(tipo)
        self._actualizar_tipo_botones()
        self._cargar_grilla()

    def _actualizar_tipo_botones(self):
        for tipo, boton in self.tipo_buttons.items():
            activo = tipo == self.tipo_actual.get()
            boton.configure(
                fg_color=C_BLUE if activo else C_BLUE_FAINT,
                text_color="white" if activo else C_NAVY,
                hover_color=C_NAVY if activo else C_BLUE,
            )

    def _tipo_columna(self):
        for etiqueta, columna in self.TIPOS_REGISTRO:
            if etiqueta == self.tipo_actual.get():
                return columna
        return "horas"

    def _parse_horas(self, txt):
        return parse_horas(txt)

    def _on_cambio(self, fecha_str, var):
        nombre = self.empleado_actual.get()
        if not nombre:
            return
        txt = var.get().strip()
        try:
            horas = self._parse_horas(txt)
        except ValueError:
            horas = 0.0
        tipo = self._tipo_columna()
        horas_guardadas = self._guardar_horas_y_split(nombre, fecha_str, tipo, horas)
        var.set(decimal_a_tiempo(horas_guardadas) if horas_guardadas > 0 else "")
        mes, anio = self.get_mes_anio()
        db_sincronizar_total_diario(nombre, mes, anio)
        self._actualizar_resumen()
        app = self.winfo_toplevel()
        app.empleados = db_cargar_mes(mes, anio)
        app._refrescar_stats()
        app._refrescar_tabla()

    def _guardar_horas_y_split(self, nombre, fecha_str, tipo, horas):
        if tipo == "horas":
            fecha = date.fromisoformat(fecha_str)
            weekday = fecha.weekday()
            
            if weekday < 5:  # Lunes a Viernes
                limite = 8.0
            else:  # Sábado y Domingo
                limite = 4.0
                
            if horas > limite:
                horas_diarias = limite
                horas_extras = horas - limite
            else:
                horas_diarias = horas
                horas_extras = 0.0
                
            db_guardar_registro_dia(nombre, fecha_str, "horas", horas_diarias)
            db_guardar_registro_dia(nombre, fecha_str, "hrs_extras", horas_extras)
            return horas_diarias
        else:
            db_guardar_registro_dia(nombre, fecha_str, tipo, horas)
            return horas

    def _actualizar_resumen(self):
        nombre = self.empleado_actual.get()
        if not nombre:
            for key in self.res_labels:
                self.res_labels[key].configure(text="—")
            return

        mes, anio = self.get_mes_anio()
        reg_horas = db_cargar_registro_diario(nombre, mes, anio, "horas")
        reg_extras = db_cargar_registro_diario(nombre, mes, anio, "hrs_extras")
        reg_noct = db_cargar_registro_diario(nombre, mes, anio, "hrs_noct")

        valores_horas = [v for v in reg_horas.values() if v > 0]
        dias = len(valores_horas)
        total_horas = sum(valores_horas)
        prom = total_horas / dias if dias else 0

        total_extras = sum(v for v in reg_extras.values() if v > 0)
        total_noct = sum(v for v in reg_noct.values() if v > 0)

        self.res_labels["dias"].configure(text=str(dias))
        self.res_labels["total"].configure(text=f"{total_horas:.1f} hs")
        self.res_labels["promedio"].configure(text=f"{prom:.1f} hs")
        self.res_labels["extras"].configure(text=f"{total_extras:.1f} hs")
        self.res_labels["nocturnas"].configure(text=f"{total_noct:.1f} hs")
