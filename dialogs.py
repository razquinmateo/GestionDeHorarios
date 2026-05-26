import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from constantes import C_BLUE, C_NAVY, COLS_EDITAR, C_GRAY600
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
        self.entries_datos_originales = datos
        self.entries = {}

        ctk.CTkLabel(self, text=titulo, font=ctk.CTkFont(size=17, weight="bold")).pack(
            pady=(24, 18)
        )

        if not solo_nombre:
            ctk.CTkLabel(
                self,
                text="⚠️ Los cambios guardados aquí reemplazan\nlos datos del registro diario de este mes.",
                font=ctk.CTkFont(size=11),
                text_color=C_GRAY600,
                justify="center",
            ).pack(pady=(0, 12))

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
            grid = ctk.CTkFrame(frame, fg_color="transparent")
            grid.pack(fill="x", pady=(12, 0))
            grid.columnconfigure(0, weight=1)
            grid.columnconfigure(1, weight=1)

            for key, label_text, hint, columna in [
                ("Horas", "Horas totales", "Ej: 90 o EL MES", 0),
                ("Hrs. Extras", "Hrs. Extras", "Ej: 15.5", 1),
            ]:
                sub = ctk.CTkFrame(grid, fg_color="transparent")
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

                if key == "Horas":
                    ToolTip(
                        entry,
                        "Horas totales del mes.",
                    )

            bottom_grid = ctk.CTkFrame(frame, fg_color="transparent")
            bottom_grid.pack(fill="x", pady=(0, 0))
            bottom_grid.columnconfigure(0, weight=1)
            bottom_grid.columnconfigure(1, weight=1)

            for key, label_text, hint, columna in [
                ("Hrs. Noct.", "Hrs. Noct.", "Ej: 8", 0),
                ("Adelanto", "Adelanto", "Ej: 10000", 1),
            ]:
                sub = ctk.CTkFrame(bottom_grid, fg_color="transparent")
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
        alto = 200 if solo_nombre else 560
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
                            if col == "Adelanto" and "+" in val:
                                partes = val.split("+")
                                val = str(sum(float(p.strip()) for p in partes))
                            else:
                                float(val)
                        except ValueError:
                            messagebox.showwarning(
                                "Valor inválido",
                                f"'{val}' no es un número válido para {col}.",
                                parent=self,
                            )
                            return
                    self.result[col] = val
        self.destroy()
