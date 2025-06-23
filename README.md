# tool_clone_github

Proyecto CLI para clonar repositorios de GitHub usando SSH, gestionando claves y configuración en ~/.ssh/config, con interfaz terminal (rich, InquirerPy) y selección de carpeta por GUI (tkinter).

## Uso

Ejecuta:

```
python app.py
```

## Requisitos

- Python 3.8+
- Git
- OpenSSH

## Instalación de dependencias

```
pip install -r requirements.txt
```

## Flujo principal

1. Muestra proyectos registrados en ~/.ssh/config
2. Permite crear un nuevo alias/proyecto
3. Genera clave SSH y actualiza ~/.ssh/config
4. Agrega clave al ssh-agent
5. Copia clave pública al portapapeles
6. Espera confirmación de usuario
7. Prueba conexión SSH
8. Solicita URL de GitHub
9. Selecciona carpeta de destino (tkinter)
10. Clona el repositorio usando el alias
11. Abre la carpeta clonada
12. Pregunta si deseas clonar otro proyecto
