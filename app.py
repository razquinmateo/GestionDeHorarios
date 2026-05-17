import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from datetime import date

from constantes import (
    C_NAVY, C_BLUE, C_BLUE_MID, C_BLUE_LIGHT, C_BLUE_FAINT,
    C_GRAY50, C_GRAY200, C_GRAY400, C_GRAY600, C_GRAY800,
    C_RED, COLS, COL_WIDTHS, MESES, EXCEL_DEFAULT,
)
from db import (
    db_inicializar, db_importar_excel, db_cargar_mes,
    db_guardar_fila, db_agregar_empleado, db_eliminar_empleado,
    db_connect,
)
from excel import excel_exportar, excel_importar, calcular_totales
from dialogs import DialogEmpleado
from registro import FrameRegistro

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class AppHorarios(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lalo Servicios — Gestión de horarios")
        try:
            self.iconbitmap("favicon.ico")
        except Exception:
            pass

        self.minsize(800, 520)
        self.update_idletasks()
        ancho = 980
        alto  = 660
        x = (self.winfo_screenwidth()  // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto  // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        hoy              = date.today()
        self.mes_actual  = hoy.month
        self.anio_actual = hoy.year
        self.empleados   = []
        self.busqueda    = tk.StringVar()
        self.busqueda.trace_add("write", lambda *_: self._filtrar())

        db_inicializar()
        self._migrar_excel_si_necesario()
        self._construir_ui()
        self._cargar_mes(self.mes_actual, self.anio_actual)
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    def _migrar_excel_si_necesario(self):
        base = os.path.dirname(
            sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
        )
        ruta = os.path.join(base, EXCEL_DEFAULT)
        if os.path.exists(ruta):
            db_importar_excel(ruta)

    # ── UI ────────────────────────────────────────────────────────────
    def _construir_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, width=190, corner_radius=0, fg_color=C_NAVY)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="  Lalo Servicios",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FFFFFF", anchor="w",
        ).pack(fill="x", padx=10, pady=(20, 2))
        ctk.CTkLabel(
            sidebar, text="  Gestión de horarios",
            font=ctk.CTkFont(size=11),
            text_color=C_GRAY400, anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 16))
        ctk.CTkFrame(sidebar, height=1, fg_color="#1A3F7A").pack(fill="x", pady=(0, 8))

        self.nav_btns = {}
        for key, label, icon in [
            ("empleados", "Empleados",      "👥"),
            ("registro",  "Registro diario","📅"),
            ("resumen",   "Resumen",        "📊"),
        ]:
            btn = ctk.CTkButton(
                sidebar, text=f"  {icon}  {label}", anchor="w",
                fg_color="transparent", text_color=C_GRAY400,
                hover_color="#1A3F7A", font=ctk.CTkFont(size=14), height=38,
                command=lambda k=key: self._cambiar_seccion(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_btns[key] = btn

        ctk.CTkFrame(sidebar, height=1, fg_color="#1A3F7A").pack(fill="x", pady=8, side="bottom")
        for texto, cmd in [
            ("  💾  Exportar Excel", self._exportar_excel),
            ("  📂  Importar Excel", self._importar_excel),
        ]:
            ctk.CTkButton(
                sidebar, text=texto, anchor="w",
                fg_color="transparent", text_color=C_GRAY400,
                hover_color="#1A3F7A", font=ctk.CTkFont(size=14), height=38,
                command=cmd,
            ).pack(fill="x", padx=8, pady=2, side="bottom")

        # ── Área principal ────────────────────────────────────────────
        self.main = ctk.CTkFrame(self, fg_color=C_GRAY50, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        # Selector de mes
        nav_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        nav_frame.grid(row=0, column=0, padx=16, pady=(14, 0), sticky="ew")
        ctk.CTkButton(nav_frame, text="◀", width=32, height=28, command=self._mes_anterior).pack(side="left")
        self.lbl_mes = ctk.CTkLabel(
            nav_frame, text="", font=ctk.CTkFont(size=15, weight="bold"), width=200
        )
        self.lbl_mes.pack(side="left", padx=8)
        ctk.CTkButton(nav_frame, text="▶", width=32, height=28, command=self._mes_siguiente).pack(side="left")
        ctk.CTkButton(
            nav_frame, text="Hoy", width=50, height=28,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"), command=self._ir_a_hoy,
        ).pack(side="left", padx=(12, 0))

        # Stats
        self.stats_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, padx=16, pady=(10, 8), sticky="ew")
        self.stat_labels = {}
        for i, (key, titulo) in enumerate([
            ("empleados","Empleados"),
            ("horas",    "Horas totales"),
            ("extras",   "Hrs. extras"),
            ("adelantos","Adelantos"),
        ]):
            self.stats_frame.columnconfigure(i, weight=1)
            card = ctk.CTkFrame(self.stats_frame)
            card.grid(row=0, column=i, padx=4, sticky="ew")
            ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=11), text_color=C_GRAY600).pack(
                anchor="w", padx=12, pady=(10, 0)
            )
            lbl = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=22, weight="bold"), text_color=C_NAVY)
            lbl.pack(anchor="w", padx=12, pady=(0, 10))
            self.stat_labels[key] = lbl

        # ── Frame empleados ───────────────────────────────────────────
        self.frame_empleados = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_empleados.grid(row=2, column=0, sticky="nsew")
        self.frame_empleados.grid_columnconfigure(0, weight=1)
        self.frame_empleados.grid_rowconfigure(0, weight=0)
        self.frame_empleados.grid_rowconfigure(1, weight=1)
        self.frame_empleados.grid_rowconfigure(2, weight=0)

        toolbar = ctk.CTkFrame(self.frame_empleados, fg_color="transparent")
        toolbar.grid(row=0, column=0, padx=16, pady=(0, 6), sticky="new")
        ctk.CTkEntry(toolbar, placeholder_text="Buscar empleado...", textvariable=self.busqueda, width=200).pack(side="left")
        ctk.CTkButton(toolbar, text="+ Nuevo", width=90, fg_color=C_BLUE, hover_color=C_NAVY, text_color="white", command=self._nuevo_empleado).pack(side="left", padx=(8, 0))
        ctk.CTkButton(toolbar, text="✏ Editar", width=90, fg_color="white", hover_color=C_BLUE_LIGHT, border_width=1, border_color=C_GRAY200, text_color=C_GRAY800, command=self._editar_empleado).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="🗑 Eliminar", width=90, fg_color="white", hover_color="#FEE2E2", border_width=1, border_color=C_GRAY200, text_color=C_RED, command=self._eliminar_empleado).pack(side="left")

        tree_frame = ctk.CTkFrame(self.frame_empleados)
        tree_frame.grid(row=1, column=0, padx=16, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview", font=("Segoe UI", 11), rowheight=32, background="#ffffff", fieldbackground="#ffffff", foreground=C_GRAY800)
        style.configure("Custom.Treeview.Heading", font=("Segoe UI", 12, "bold"), background=C_BLUE_FAINT, foreground=C_GRAY600, relief="flat", padding=(0, 6))
        style.map("Custom.Treeview", background=[("selected", C_BLUE_LIGHT)], foreground=[("selected", C_NAVY)])

        self.tree = ttk.Treeview(tree_frame, columns=COLS, show="headings", style="Custom.Treeview", selectmode="browse")
        for col, w in zip(COLS, COL_WIDTHS):
            self.tree.heading(col, text=col)
            anchor = "w" if col in ("Empleado", "Observaciones") else "center"
            self.tree.column(col, width=w, minwidth=50, anchor=anchor)

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", lambda e: self._editar_empleado() if self.tree.selection() else None)
        self.tree.bind("<Return>",   lambda e: self._editar_empleado() if self.tree.selection() else None)
        self.tree.bind("<Delete>",   lambda e: self._eliminar_empleado() if self.tree.selection() else None)
        self.tree.bind("<<TreeviewSelect>>", self._actualizar_panel_obs)

        panel = ctk.CTkFrame(self.frame_empleados, fg_color="white", border_width=1, border_color=C_GRAY200)
        panel.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="ew")
        panel.grid_columnconfigure(0, weight=1)

        header_obs = ctk.CTkFrame(panel, fg_color="transparent")
        header_obs.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        header_obs.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header_obs, text="OBSERVACIONES", font=ctk.CTkFont(size=10, weight="bold"), text_color=C_BLUE).grid(row=0, column=0, sticky="w")
        self.lbl_panel_emp = ctk.CTkLabel(header_obs, text="", font=ctk.CTkFont(size=11), text_color=C_GRAY600, anchor="e")
        self.lbl_panel_emp.grid(row=0, column=1, sticky="e")
        self.txt_obs = ctk.CTkTextbox(panel, height=72, font=ctk.CTkFont(size=13), wrap="word", state="disabled", fg_color="transparent", border_width=0, text_color=C_GRAY800)
        self.txt_obs.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

        # ── Frame resumen ─────────────────────────────────────────────
        self.frame_resumen = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_resumen.grid(row=2, column=0, sticky="nsew")
        self.frame_resumen.grid_columnconfigure(0, weight=1)
        self.frame_resumen.grid_rowconfigure(0, weight=1)
        self.frame_resumen.grid_rowconfigure(1, weight=1)
        self.frame_resumen.grid_remove()

        # ── Frame registro diario ─────────────────────────────────────
        self.frame_registro = FrameRegistro(
            self.main, get_mes_anio=lambda: (self.mes_actual, self.anio_actual)
        )
        self.frame_registro.grid(row=2, column=0, sticky="nsew")
        self.frame_registro.grid_remove()

        self._cambiar_seccion("empleados")

    # ── Navegación mes ────────────────────────────────────────────────
    def _actualizar_label_mes(self):
        self.lbl_mes.configure(text=f"{MESES[self.mes_actual - 1]} {self.anio_actual}")

    def _mes_anterior(self):
        self.mes_actual, self.anio_actual = (
            (12, self.anio_actual - 1) if self.mes_actual == 1
            else (self.mes_actual - 1, self.anio_actual)
        )
        self._cargar_mes(self.mes_actual, self.anio_actual)

    def _mes_siguiente(self):
        self.mes_actual, self.anio_actual = (
            (1, self.anio_actual + 1) if self.mes_actual == 12
            else (self.mes_actual + 1, self.anio_actual)
        )
        self._cargar_mes(self.mes_actual, self.anio_actual)

    def _ir_a_hoy(self):
        hoy = date.today()
        self._cargar_mes(hoy.month, hoy.year)

    # ── Navegación secciones ──────────────────────────────────────────
    def _cambiar_seccion(self, key):
        for k, btn in self.nav_btns.items():
            btn.configure(
                fg_color=C_BLUE if k == key else "transparent",
                text_color="white" if k == key else C_GRAY400,
            )
        self.frame_empleados.grid_remove()
        self.frame_resumen.grid_remove()
        self.frame_registro.grid_remove()

        if key == "empleados":
            self.frame_empleados.grid()
        elif key == "resumen":
            self.frame_resumen.grid()
            self._refrescar_resumen()
        elif key == "registro":
            self.frame_registro.grid()
            self.frame_registro.refrescar()

    # ── Datos ─────────────────────────────────────────────────────────
    def _cargar_mes(self, mes, anio):
        self.mes_actual  = mes
        self.anio_actual = anio
        self._actualizar_label_mes()
        self.empleados = db_cargar_mes(mes, anio)
        self._refrescar_tabla()
        self._refrescar_stats()
        if self.frame_registro.winfo_ismapped():
            self.frame_registro.refrescar()

    def _refrescar_tabla(self, filtro=""):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for emp in self.empleados:
            if filtro.lower() in emp["Empleado"].lower():
                origen = emp.get("Origen", "manual")
                vals = [
                    emp["Empleado"],
                    emp["Horas"],
                    emp["Hrs. Extras"],
                    emp["Hrs. Noct."],
                    emp["Adelanto"],
                ]
                if str(emp["Horas"]).upper().strip().startswith("EL MES"):
                    tag = "mes"
                elif origen == "diario":
                    tag = "diario"
                else:
                    tag = ""
                self.tree.insert("", "end", values=vals, tags=(tag,))
        self.tree.tag_configure("mes",    foreground="#854F0B", background="#FAEEDA")
        self.tree.tag_configure("diario", foreground=C_NAVY,   background=C_BLUE_LIGHT)

    def _refrescar_stats(self):
        t = calcular_totales(self.empleados)
        self.stat_labels["empleados"].configure(text=str(t["empleados"]))
        self.stat_labels["horas"].configure(text=f"{t['horas']:.1f}")
        self.stat_labels["extras"].configure(text=f"{t['extras']:.1f}")
        self.stat_labels["adelantos"].configure(text=f"${t['adelantos']:,.0f}".replace(",", "."))

    def _filtrar(self):
        self._refrescar_tabla(self.busqueda.get())

    def _actualizar_panel_obs(self, event=None):
        sel = self.tree.selection()
        if not sel:
            self.lbl_panel_emp.configure(text="")
            self.txt_obs.configure(state="normal")
            self.txt_obs.delete("1.0", "end")
            self.txt_obs.configure(state="disabled")
            return
        nombre = self.tree.item(sel[0], "values")[0]
        emp    = next((e for e in self.empleados if e["Empleado"] == nombre), None)
        if emp is None:
            return
        self.lbl_panel_emp.configure(text=nombre)
        texto = emp["Observaciones"].strip()
        self.txt_obs.configure(state="normal")
        self.txt_obs.delete("1.0", "end")
        self.txt_obs.insert("1.0", texto if texto else "Sin observaciones.")
        self.txt_obs.configure(state="disabled")

    # ── CRUD ──────────────────────────────────────────────────────────
    def _nuevo_empleado(self):
        dlg = DialogEmpleado(self, "Nuevo empleado", solo_nombre=True)
        self.wait_window(dlg)
        if dlg.result:
            if db_agregar_empleado(dlg.result["Empleado"], self.mes_actual, self.anio_actual):
                self._cargar_mes(self.mes_actual, self.anio_actual)

    def _empleado_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Sin selección", "Seleccioná un empleado primero.")
            return None, None
        item   = sel[0]
        nombre = self.tree.item(item, "values")[0]
        idx    = next((i for i, e in enumerate(self.empleados) if e["Empleado"] == nombre), None)
        return idx, item

    def _editar_empleado(self):
        idx, _ = self._empleado_seleccionado()
        if idx is None:
            return
        emp_original = self.empleados[idx]
        dlg = DialogEmpleado(self, f"Editar — {emp_original['Empleado']}", datos=emp_original)
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["Empleado"] = emp_original["Empleado"]
            dlg.result["Origen"]   = emp_original.get("Origen", "manual")
            self.empleados[idx]    = dlg.result
            db_guardar_fila(emp_original["Empleado"], self.mes_actual, self.anio_actual, dlg.result)
            self._refrescar_tabla(self.busqueda.get())
            self._refrescar_stats()
            for item in self.tree.get_children():
                if self.tree.item(item, "values")[0] == emp_original["Empleado"]:
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    self._actualizar_panel_obs()
                    break

    def _eliminar_empleado(self):
        idx, _ = self._empleado_seleccionado()
        if idx is None:
            return
        nombre = self.empleados[idx]["Empleado"]
        if messagebox.askyesno(
            "Confirmar",
            f"¿Dar de baja a {nombre}?\n\n"
            "Sus datos históricos se conservan pero no aparecerá en meses nuevos.",
        ):
            db_eliminar_empleado(nombre)
            self._cargar_mes(self.mes_actual, self.anio_actual)

    # ── Importar / Exportar ───────────────────────────────────────────
    def _exportar_excel(self):
        carpeta_inicial = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.exists(carpeta_inicial):
            carpeta_inicial = os.path.expanduser("~")
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=f"planilla_{MESES[self.mes_actual-1]}_{self.anio_actual}.xlsx",
            initialdir=carpeta_inicial,
            filetypes=[("Excel", "*.xlsx")],
        )
        if not path:
            return
        try:
            excel_exportar(path, self.empleados, self.mes_actual, self.anio_actual)
            messagebox.showinfo("Exportado", f"Planilla guardada en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e))

    def _importar_excel(self):
        path = filedialog.askopenfilename(
            title="Seleccionar Excel a importar",
            filetypes=[("Excel", "*.xlsx *.xls")],
        )
        if not path:
            return
        try:
            datos = excel_importar(path)
        except Exception as e:
            messagebox.showerror("Error al leer el archivo", str(e))
            return
        if not datos:
            messagebox.showwarning("Sin datos", "No se encontraron datos en el archivo.")
            return
        resp = messagebox.askyesnocancel(
            "Importar datos",
            f"Se encontraron {len(datos)} empleados.\n\n"
            f"¿Desea REEMPLAZAR los datos de {MESES[self.mes_actual-1]} {self.anio_actual}?\n\n"
            "Sí = reemplazar     No = agregar al final     Cancelar = cancelar",
        )
        if resp is None:
            return
        con = db_connect()
        cur = con.cursor()
        for emp in datos:
            nombre = emp["Empleado"]
            cur.execute("INSERT OR IGNORE INTO empleados (nombre) VALUES (?)", (nombre,))
            emp_id = cur.execute("SELECT id FROM empleados WHERE nombre=?", (nombre,)).fetchone()[0]
            cur.execute("UPDATE empleados SET activo=1 WHERE id=?", (emp_id,))
            if resp:
                cur.execute("DELETE FROM planillas WHERE empleado_id=? AND mes=? AND anio=?", (emp_id, self.mes_actual, self.anio_actual))
            cur.execute(
                "INSERT OR IGNORE INTO planillas (empleado_id, mes, anio, horas, hrs_extras, hrs_noct, adelanto, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (emp_id, self.mes_actual, self.anio_actual, emp["Horas"], emp["Hrs. Extras"], emp["Hrs. Noct."], emp["Adelanto"], emp["Observaciones"]),
            )
        con.commit()
        con.close()
        self._cargar_mes(self.mes_actual, self.anio_actual)
        messagebox.showinfo("Listo", f"Se importaron {len(datos)} empleados.")

    # ── Resumen ───────────────────────────────────────────────────────
    def _refrescar_resumen(self):
        for widget in self.frame_resumen.winfo_children():
            widget.destroy()
        self.frame_resumen.grid_rowconfigure(0, weight=1)
        self.frame_resumen.grid_rowconfigure(1, weight=1)
        self._construir_tabla_anual()
        self._construir_ranking()

    def _construir_tabla_anual(self):
        frame = ctk.CTkFrame(self.frame_resumen)
        frame.grid(row=0, column=0, columnspan=2, padx=16, pady=(8, 6), sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame, text=f"Resumen anual {self.anio_actual}", font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        cols_res = ["Mes", "Empleados", "Horas", "Hrs. Extras", "Adelantos"]
        widths   = [120, 90, 90, 110, 110]

        style = ttk.Style()
        style.configure("Resumen.Treeview", font=("Segoe UI", 11), rowheight=28, background="#ffffff", fieldbackground="#ffffff", foreground="#1a1a1a")
        style.configure("Resumen.Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#f4f4f4", foreground="#333333", relief="flat", padding=(0, 4))
        style.map("Resumen.Treeview", background=[("selected", "#cfe2ff")], foreground=[("selected", "#0a3880")])

        tree_wrap = ctk.CTkFrame(frame, fg_color="transparent")
        tree_wrap.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        tree_wrap.grid_columnconfigure(0, weight=1)
        tree_wrap.grid_rowconfigure(0, weight=1)

        tree = ttk.Treeview(tree_wrap, columns=cols_res, show="headings", style="Resumen.Treeview", selectmode="none", height=12)
        for col, w in zip(cols_res, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.column("Mes", anchor="w")

        adel_acum = 0
        for m in range(1, 13):
            datos       = db_cargar_mes(m, self.anio_actual)
            tiene_datos = any(e["Horas"] or e["Hrs. Extras"] or e["Adelanto"] for e in datos)
            if not tiene_datos:
                tree.insert("", "end", values=(MESES[m - 1], "—", "—", "—", "—"), tags=("futuro",))
                continue
            t = calcular_totales(datos)
            adel_acum += t["adelantos"]
            tag = "actual" if m == self.mes_actual else ""
            tree.insert("", "end", values=(
                MESES[m - 1], t["empleados"],
                f"{t['horas']:.1f}", f"{t['extras']:.1f}",
                f"${t['adelantos']:,.0f}".replace(",", "."),
            ), tags=(tag,))

        tree.tag_configure("actual", background="#cfe2ff", foreground="#0a3880")
        tree.tag_configure("futuro", foreground="#aaaaaa")
        scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        ctk.CTkLabel(
            frame,
            text=f"Adelantos acumulados {self.anio_actual}:  ${adel_acum:,.0f}".replace(",", "."),
            font=ctk.CTkFont(size=13, weight="bold"), text_color=C_NAVY, anchor="e",
        ).grid(row=2, column=0, padx=12, pady=(4, 10), sticky="e")

    def _construir_ranking(self):
        datos_mes = db_cargar_mes(self.mes_actual, self.anio_actual)
        ranking   = []
        for emp in datos_mes:
            val = emp["Horas"].replace(" ", "")
            try:
                ranking.append((emp["Empleado"], float(val)))
            except ValueError:
                pass
        ranking.sort(key=lambda x: x[1], reverse=True)

        frame = ctk.CTkFrame(self.frame_resumen)
        frame.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame, text=f"Top horas — {MESES[self.mes_actual-1]} {self.anio_actual}", font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(row=0, column=0, padx=12, pady=(10, 8), sticky="w")

        if not ranking:
            ctk.CTkLabel(frame, text="Sin datos numéricos de horas este mes.", text_color="gray").grid(row=1, column=0, padx=12, pady=8)
            return

        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent", height=160)
        scroll_frame.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="nsew")
        scroll_frame.grid_columnconfigure(1, weight=1)

        max_horas = ranking[0][1]
        for i, (nombre, horas) in enumerate(ranking):
            ctk.CTkLabel(scroll_frame, text=nombre, width=160, anchor="w", font=ctk.CTkFont(size=12)).grid(row=i, column=0, pady=4, sticky="w")
            barra_bg = ctk.CTkFrame(scroll_frame, height=18, fg_color=("gray88", "gray25"), corner_radius=4)
            barra_bg.grid(row=i, column=1, padx=(8, 8), pady=4, sticky="ew")
            barra_bg.grid_propagate(False)
            pct   = horas / max_horas
            color = C_BLUE if i == 0 else C_BLUE_MID
            barra = ctk.CTkFrame(barra_bg, height=18, fg_color=color, corner_radius=4)
            barra.place(relx=0, rely=0, relwidth=pct, relheight=1)
            ctk.CTkLabel(scroll_frame, text=f"{horas:.1f} hs", width=60, anchor="e", font=ctk.CTkFont(size=12)).grid(row=i, column=2, pady=4, sticky="e")

    # ── Cierre ────────────────────────────────────────────────────────
    def _al_cerrar(self):
        resp = messagebox.askyesnocancel(
            "Cerrar aplicación",
            "¿Desea exportar la planilla actual a Excel antes de cerrar?\n\n"
            "Los datos ya están guardados en la base de datos.",
        )
        if resp is None:
            return
        if resp:
            self._exportar_excel()
        self.destroy()
