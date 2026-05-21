import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

from constantes import C_BLUE, C_NAVY, COLS_EDITAR
from registro import parse_horas


class ToolTip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.id = None
        self.tw = None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")
        widget.bind("<Motion>", self._motion, add="+")

    def _enter(self, event=None):
        self._schedule()

    def _leave(self, event=None):
        self._unschedule()
        self._hide()

    def _motion(self, event=None):
        if self.tw:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            self.tw.wm_geometry(f"+{x}+{y}")

    def _schedule(self):
        self._unschedule()
        self.id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def _show(self):
        if self.tw or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_attributes("-topmost", True)
        label = tk.Label(
            self.tw,
            text=self.text,
            justify="left",
            background="#FFFFE0",
            relief="solid",
            borderwidth=1,
            font=("Arial", 10),
            wraplength=220,
        )
        label.pack(ipadx=6, ipady=4)
        self.tw.wm_geometry(f"+{x}+{y}")

    def _hide(self):
        if self.tw:
            self.tw.destroy()
            self.tw = None


class DialogEmpleado(ctk.CTkToplevel):
    def __init__(self, parent, titulo="Nuevo empleado", datos=None, solo_nombre=False):
        super().__init__(parent)
        self.title(titulo)
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self.solo_nombre = solo_nombre
        datos = datos or {}
        self.entries = {}

        ctk.CTkLabel(self, text=titulo, font=ctk.CTkFont(size=17, weight="bold")).pack(
            pady=(24, 18)
        )

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=36)

        ctk.CTkLabel(
            frame, text="Empleado", font=ctk.CTkFont(size=13), anchor="w"
        ).pack(fill="x", pady=(0, 2))
        entry_emp = ctk.CTkEntry(
            frame,
            placeholder_text="Nombre completo",
            height=36,
            font=ctk.CTkFont(size=13),
        )
        entry_emp.pack(fill="x")
        if datos.get("Empleado"):
            entry_emp.insert(0, datos["Empleado"])
        self.entries["Empleado"] = entry_emp

        if not solo_nombre:
            top_grid = ctk.CTkFrame(frame, fg_color="transparent")
            top_grid.pack(fill="x", pady=(12, 0))
            top_grid.columnconfigure(0, weight=1)
            top_grid.columnconfigure(1, weight=1)

            for key, label_text, hint, columna in [
                ("Horas diarias", "Horas diarias", "Ej: 8 o 8-16", 0),
                ("Horas", "Horas totales", "Ej: 90 o EL MES", 1),
            ]:
                sub = ctk.CTkFrame(top_grid, fg_color="transparent")
                sub.grid(
                    row=0,
                    column=columna,
                    padx=(0, 6) if columna == 0 else 0,
                    pady=4,
                    sticky="ew",
                )
                ctk.CTkLabel(
                    sub, text=label_text, font=ctk.CTkFont(size=13), anchor="w"
                ).pack(fill="x", pady=(0, 2))
                entry = ctk.CTkEntry(
                    sub, placeholder_text=hint, height=36, font=ctk.CTkFont(size=13)
                )
                entry.pack(fill="x")
                if datos.get(key):
                    entry.insert(0, datos[key])
                self.entries[key] = entry

                if key == "Horas diarias":
                    ToolTip(
                        entry,
                        "Ingresa un número o un rango como 8-16 o 8:16.\nSe sumará a las horas totales.",
                    )
                elif key == "Horas":
                    ToolTip(
                        entry,
                        "Horas totales del mes.\nSi también ingresas horas diarias, esas se suman al total.",
                    )

            grid = ctk.CTkFrame(frame, fg_color="transparent")
            grid.pack(fill="x", pady=(0, 0))
            grid.columnconfigure(0, weight=1)
            grid.columnconfigure(1, weight=1)
            grid.columnconfigure(2, weight=1)

            for key, label_text, hint, columna in [
                ("Hrs. Extras", "Hrs. Extras", "Ej: 15.5", 0),
                ("Hrs. Noct.", "Hrs. Noct.", "Ej: 8", 1),
                ("Adelanto", "Adelanto", "Ej: 10000", 2),
            ]:
                sub = ctk.CTkFrame(grid, fg_color="transparent")
                sub.grid(
                    row=0,
                    column=columna,
                    padx=(0, 6) if columna != 2 else 0,
                    pady=4,
                    sticky="ew",
                )
                ctk.CTkLabel(
                    sub, text=label_text, font=ctk.CTkFont(size=13), anchor="w"
                ).pack(fill="x", pady=(0, 2))
                entry = ctk.CTkEntry(
                    sub, placeholder_text=hint, height=36, font=ctk.CTkFont(size=13)
                )
                entry.pack(fill="x")
                if datos.get(key):
                    entry.insert(0, datos[key])
                self.entries[key] = entry

            ctk.CTkLabel(
                frame, text="Observaciones", font=ctk.CTkFont(size=13), anchor="w"
            ).pack(fill="x", pady=(14, 2))
            txt = ctk.CTkTextbox(
                frame, height=100, font=ctk.CTkFont(size=13), wrap="word"
            )
            txt.pack(fill="x")
            if datos.get("Observaciones"):
                txt.insert("1.0", datos["Observaciones"])
            self.entries["Observaciones"] = txt

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=36, pady=20)
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray70"),
            height=38,
            font=ctk.CTkFont(size=13),
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            btn_frame,
            text="Guardar",
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color=C_BLUE,
            hover_color=C_NAVY,
            text_color="white",
            command=self._guardar,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.update_idletasks()
        ancho = 440
        alto = 200 if solo_nombre else 520
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (ancho // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        def _on_return(e):
            if not isinstance(self.focus_get(), ctk.CTkTextbox):
                self._guardar()
                return "break"

        self.bind("<Return>", _on_return)
        self.bind("<Escape>", lambda e: self.destroy())

    def _guardar(self):
        nombre = self.entries["Empleado"].get().strip()
        if not nombre:
            messagebox.showwarning(
                "Atención", "El nombre no puede estar vacío.", parent=self
            )
            return
        if self.solo_nombre:
            self.result = {"Empleado": nombre}
        else:
            self.result = {}

            horas_diarias_txt = self.entries["Horas diarias"].get().strip()
            horas_diarias = 0.0
            if horas_diarias_txt:
                try:
                    horas_diarias = parse_horas(horas_diarias_txt)
                except ValueError:
                    messagebox.showwarning(
                        "Valor inválido",
                        f"'{horas_diarias_txt}' no es un valor válido para Horas diarias.",
                        parent=self,
                    )
                    return

            for col in COLS_EDITAR:
                widget = self.entries[col]
                if col == "Observaciones":
                    self.result[col] = widget.get("1.0", "end").strip()
                elif col == "Horas":
                    val = widget.get().strip().upper()
                    if val and val != "EL MES":
                        try:
                            float(val)
                        except ValueError:
                            messagebox.showwarning(
                                "Valor inválido",
                                f"'{val}' no es un número válido para Horas totales.",
                                parent=self,
                            )
                            return
                    self.result[col] = val
                else:
                    val = widget.get().strip()
                    if val and col in ("Hrs. Extras", "Hrs. Noct.", "Adelanto"):
                        try:
                            float(val)
                        except ValueError:
                            messagebox.showwarning(
                                "Valor inválido",
                                f"'{val}' no es un número válido para {col}.",
                                parent=self,
                            )
                            return
                    self.result[col] = val

            if horas_diarias:
                horas_totales = self.result.get("Horas", "")
                if horas_totales.upper() == "EL MES":
                    messagebox.showwarning(
                        "Atención",
                        "No se puede sumar Horas diarias cuando Horas totales es EL MES.",
                        parent=self,
                    )
                    return
                try:
                    base = float(horas_totales) if horas_totales else 0.0
                except ValueError:
                    messagebox.showwarning(
                        "Valor inválido",
                        f"'{horas_totales}' no es un número válido para Horas totales.",
                        parent=self,
                    )
                    return
                total = base + horas_diarias
                self.result["Horas"] = (
                    str(int(total)) if total == int(total) else str(total)
                )
        self.destroy()
