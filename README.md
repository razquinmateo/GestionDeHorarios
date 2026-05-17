# Gestión de horarios

Aplicación de escritorio para gestionar la planilla de sueldos y horarios de empleados.

---

## Requisitos

- Python 3.8 o superior (https://www.python.org/downloads/)
- Windows 10/11

---

## Instalación (primera vez)

Abrí una terminal (CMD o PowerShell) y ejecutá:

```
pip install customtkinter openpyxl
```

---

## Cómo usar

1. Colocá el archivo `planilla.xlsx` en la misma carpeta que `main.py` (solo la primera vez, para migrar datos)
2. Hacé doble clic en `iniciar.bat` (o ejecutá `python main.py` desde la terminal)

---

## Funciones disponibles

| Función           | Cómo usarla                                         |
|-------------------|-----------------------------------------------------|
| Ver empleados     | Se carga automáticamente al abrir                   |
| Buscar empleado   | Escribir en el campo de búsqueda                    |
| Agregar empleado  | Botón "+ Nuevo"                                     |
| Editar empleado   | Doble clic, Enter, o botón "Editar"                 |
| Eliminar empleado | Seleccionarlo y presionar Delete o botón "Eliminar" |
| Registro diario   | Sección "Registro diario" en el menú lateral        |
| Ver resumen anual | Sección "Resumen" en el menú lateral                |
| Exportar Excel    | Botón "Exportar Excel" en el menú lateral           |
| Importar Excel    | Botón "Importar Excel" en el menú lateral           |

---

## Estructura del proyecto

```
lalo_servicios/
├── main.py         ← entry point
├── app.py          ← ventana principal
├── constantes.py   ← colores, columnas, configuración
├── db.py           ← base de datos SQLite
├── excel.py        ← importar y exportar Excel
├── dialogs.py      ← ventana de edición de empleados
├── registro.py     ← sección de registro diario
├── favicon.ico     ← ícono de la app
├── iniciar.bat     ← acceso directo para Windows
└── README.md       ← este archivo
```

---

## Notas

- Los datos se guardan automáticamente en `horarios.db` (SQLite).
- La `planilla.xlsx` solo se usa la primera vez para migrar datos existentes.
- Al cerrar la app, se ofrece exportar la planilla del mes actual a Excel.
