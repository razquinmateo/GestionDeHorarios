import customtkinter as ctk
from tkinter import messagebox

from constantes import C_BLUE, C_NAVY, COLS_EDITAR


class DialogEmpleado(ctk.CTkToplevel):
    def __init__(self, parent, titulo="Nuevo empleado", datos=None, solo_nombre=False):
        super().__init__(parent)
        self.title(titulo)
        self.resizable(False, False)
        self.grab_set()
        self.result      = None
        self.solo_nombre = solo_nombre
        datos            = datos or {}
        self.entries     = {}

        ctk.CTkLabel(self, text=titulo, font=ctk.CTkFont(size=17, weight="bold")).pack(
            pady=(24, 18)
        )

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=36)

        ctk.CTkLabel(frame, text="Empleado", font=ctk.CTkFont(size=13), anchor="w").pack(
            fill="x", pady=(0, 2)
        )
        entry_emp = ctk.CTkEntry(
            frame, placeholder_text="Nombre completo", height=36, font=ctk.CTkFont(size=13)
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

            for col, hint, fila, columna in [
                ("Horas",      "Ej: 90 o EL MES", 0, 0),
                ("Hrs. Extras","Ej: 15.5",         0, 1),
                ("Hrs. Noct.", "Ej: 8",            1, 0),
                ("Adelanto",   "Ej: 10000",        1, 1),
            ]:
                sub = ctk.CTkFrame(grid, fg_color="transparent")
                sub.grid(
                    row=fila, column=columna,
                    padx=(0, 6) if columna == 0 else (6, 0),
                    pady=4, sticky="ew",
                )
                ctk.CTkLabel(sub, text=col, font=ctk.CTkFont(size=13), anchor="w").pack(
                    fill="x", pady=(0, 2)
                )
                entry = ctk.CTkEntry(
                    sub, placeholder_text=hint, height=36, font=ctk.CTkFont(size=13)
                )
                entry.pack(fill="x")
                if datos.get(col):
                    entry.insert(0, datos[col])
                self.entries[col] = entry

            ctk.CTkLabel(
                frame, text="Observaciones", font=ctk.CTkFont(size=13), anchor="w"
            ).pack(fill="x", pady=(14, 2))
            txt = ctk.CTkTextbox(frame, height=100, font=ctk.CTkFont(size=13), wrap="word")
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
        alto  = 200 if solo_nombre else 520
        x = parent.winfo_x() + (parent.winfo_width()  // 2) - (ancho // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (alto  // 2)
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
            messagebox.showwarning("Atención", "El nombre no puede estar vacío.", parent=self)
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
                                f"'{val}' no es un número válido para Horas.",
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
        self.destroy()
