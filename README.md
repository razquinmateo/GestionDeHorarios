# Gestión de horarios — Bargas

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

1. Colocá el archivo `planilla.xlsx` en la misma carpeta que `app.py`
2. Hacé doble clic en `iniciar.bat`  (o ejecutá `python app.py` desde la terminal)

Si la planilla no está en la misma carpeta, la app te va a pedir que la selecciones.

---

## Funciones disponibles

| Función           | Cómo usarla                                 |
|-------------------|---------------------------------------------|
| Ver empleados     | Se carga automáticamente al abrir           |
| Buscar empleado   | Escribir en el campo de búsqueda            |
| Agregar empleado  | Botón "+ Nuevo"                             |
| Editar empleado   | Seleccionarlo y hacer doble clic, o "Editar"|
| Eliminar empleado | Seleccionarlo y hacer clic en "Eliminar"    |
| Guardar Excel     | Botón "Guardar Excel" en el menú lateral    |

---

## Convertir a .exe (opcional)

Para distribuir la app sin que el usuario tenga Python instalado:

```
pip install pyinstaller
pyinstaller --onefile --windowed --name "GestionHorarios" app.py
```

El ejecutable queda en la carpeta `dist/`.

---

## Estructura del proyecto

```
app_horarios/
├── app.py          ← código principal
├── planilla.xlsx   ← tu Excel (copiar acá)
├── iniciar.bat     ← acceso directo para Windows
└── README.md       ← este archivo
```
