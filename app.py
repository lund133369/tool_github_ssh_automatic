import os
import sys
import subprocess
import shutil
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer
import pyperclip
import importlib.util
import webbrowser

console = Console()
SSH_CONFIG = os.path.expanduser("~/.ssh/config")
SSH_DIR = os.path.expanduser("~/.ssh")

# Utilidades


def leer_ssh_config():
    if not os.path.exists(SSH_CONFIG):
        return []
    proyectos = []
    with open(SSH_CONFIG, "r", encoding="utf-8") as f:
        lines = f.readlines()
    bloque = {}
    for line in lines:
        if line.startswith("# Repo:"):
            bloque["repo"] = line.strip().split(":", 1)[1].strip()
        elif line.startswith("# Ruta:"):
            bloque["ruta"] = line.strip().split(":", 1)[1].strip()
        elif line.startswith("Host "):
            bloque["alias"] = line.strip().split(" ", 1)[1].strip()
        elif line.strip().startswith("IdentityFile"):
            bloque["key"] = line.strip().split(" ", 1)[1].strip()
        elif line.strip() == "" and "alias" in bloque:
            proyectos.append(bloque)
            bloque = {}
    if "alias" in bloque:
        proyectos.append(bloque)
    return proyectos


def mostrar_proyectos(proyectos):
    table = Table(title="📂 Proyectos registrados en ~/.ssh/config:")
    table.add_column("Alias", style="cyan")
    table.add_column("Repo URL", style="magenta")
    table.add_column("Ruta Local", style="green")
    for p in proyectos:
        table.add_row(p.get("alias", ""), p.get("repo", ""), p.get("ruta", ""))
    console.print(table)


def preguntar_alias(proyectos):
    existentes = {p["alias"] for p in proyectos}
    while True:
        alias = inquirer.text(message="Nombre del proyecto (alias):").execute()
        if alias in existentes:
            console.print("[red]Ese alias ya existe en ~/.ssh/config[/red]")
        elif re.match(r"^[\w\-]+$", alias):
            return alias
        else:
            console.print(
                "[red]Alias inválido. Usa solo letras, números, guiones.[/red]"
            )


def generar_clave(alias):
    key_path = os.path.join(SSH_DIR, f"id_rsa_{alias}")
    if os.path.exists(key_path):
        sobre = inquirer.confirm(
            message=f"La clave {key_path} ya existe. ¿Sobrescribir?", default=False
        ).execute()
        if not sobre:
            return key_path
        os.remove(key_path)
        if os.path.exists(key_path + ".pub"):
            os.remove(key_path + ".pub")
    subprocess.run(
        ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", key_path, "-N", ""], check=True
    )
    return key_path


def actualizar_ssh_config(alias, repo_url, ruta, key_path):
    entrada = f"""
# Repo: {repo_url}
# Ruta: {ruta}
Host {alias}
    HostName github.com
    User git
    IdentityFile {key_path}
"""
    with open(SSH_CONFIG, "a", encoding="utf-8") as f:
        f.write(entrada)


def agregar_a_ssh_agent(key_path):
    try:
        subprocess.run(["ssh-add", key_path], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="ignore") if e.stderr else ""
        if "Error connecting to agent" in stderr:
            console.print(
                "[yellow]ssh-agent no está activo. Puedes iniciarlo manualmente si lo deseas.[/yellow]"
            )
        else:
            console.print(
                f"[yellow]No se pudo agregar la clave al ssh-agent: {stderr}[/yellow]"
            )
    # Continúa el flujo aunque falle


def copiar_clave_publica(key_path):
    pub_path = key_path + ".pub"
    with open(pub_path, "r", encoding="utf-8") as f:
        pub = f.read()
    pyperclip.copy(pub)
    console.print("[green]Clave pública copiada al portapapeles[/green]")
    console.print(pub)


def esperar_confirmacion(repo_url):
    # Extraer usuario y repo de la URL SSH
    m = re.match(r"^git@github.com:([^/]+)/([^.]+)\.git$", repo_url)
    if m:
        usuario, repo = m.group(1), m.group(2)
        url_settings = f"https://github.com/{usuario}/{repo}/settings/keys"
        console.print(
            f"[yellow]Abriendo la página de llaves SSH del repositorio:[/yellow] {url_settings}"
        )
        webbrowser.open(url_settings)
    else:
        console.print(
            "[red]No se pudo extraer usuario y repo de la URL. Abre manualmente la configuración de llaves SSH en GitHub.[/red]"
        )
    inquirer.confirm(
        message="¿Ya agregaste la clave en GitHub?", default=True
    ).execute()


def probar_conexion(alias):
    try:
        console.print(f"[cyan]Probando conexión SSH con el alias {alias}...[/cyan]")
        result = subprocess.run(
            ["ssh", "-T", alias], check=True, capture_output=True, text=True
        )
        if "successfully authenticated" in result.stdout:
            console.print(f"[green]Conexión exitosa con {alias}[/green]")
        else:
            console.print(
                f"[red]Error al conectar con {alias}: {result.stderr.strip()}[/red]"
            )
    except Exception as e:
        console.print(f"[red]Error al probar conexión con {alias}: {e}[/red]")


def pedir_repo_url():
    while True:
        url = inquirer.text(
            message="URL SSH de GitHub (git@github.com:user/repo.git):"
        ).execute()
        if re.match(r"^git@github.com:.+/.+\.git$", url):
            return url
        else:
            console.print("[red]URL inválida[/red]")


def seleccionar_carpeta():
    import sys
    import subprocess
    import os

    script_path = os.path.join(os.path.dirname(__file__), "select_folder_tk.py")
    try:
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True, timeout=30
        )
        salida = result.stdout.strip()
        console.print(f"[cyan]Ruta seleccionada: {salida}[/cyan]")
        if salida:
            console.print(f"[green]Carpeta seleccionada: {salida}[/green]")
            return salida
        print(
            "[red]No seleccionaste ninguna carpeta. Intenta de nuevo o ingresa la ruta manualmente.[/red]"
        )
        return inquirer.text(
            message="Pega aquí la ruta de la carpeta de destino:"
        ).execute()
    except Exception as e:
        print(f"[red]Error al abrir el diálogo de selección de carpeta: {e}[/red]")
        return inquirer.text(
            message="Pega aquí la ruta de la carpeta de destino:"
        ).execute()


def clonar_repo(alias, url, destino):
    try:
        console.print(
            f"[cyan]Clonando el repositorio {url} en {destino} con alias {alias}...[/cyan]"
        )
        if not os.path.exists(destino):
            os.makedirs(destino)
        ruta = os.path.join(destino, alias)
        key_path = os.path.normpath(
            os.path.expanduser(os.path.join(SSH_DIR, f"id_rsa_{alias}"))
        )
        subprocess.run(
            [
                "git",
                "clone",
                url,
                ruta,
                "--config",
                f'core.sshCommand=ssh -i "{key_path}"',
            ],
            check=True,
        )
        return ruta
    except Exception as e:
        console.print(f"[red]Error al clonar el repositorio: {e}[/red]")
        sys.exit(1)


def abrir_carpeta(ruta):
    if sys.platform.startswith("win"):
        os.startfile(ruta)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", ruta])
    elif sys.platform == "darwin":
        subprocess.run(["open", ruta])


def validar_prerequisitos():
    import platform
    import shutil

    errores = []
    # Python version
    if sys.version_info < (3, 8):
        errores.append("Python 3.8 o superior es requerido.")
    # Comandos externos
    for cmd in ["git", "ssh", "ssh-keygen"]:
        if shutil.which(cmd) is None:
            errores.append(f'El comando "{cmd}" no está disponible en el PATH.')
    # Carpeta ~/.ssh
    if not os.path.isdir(SSH_DIR):
        try:
            os.makedirs(SSH_DIR)
        except Exception:
            errores.append(f"No se pudo crear la carpeta {SSH_DIR}.")
    # Librerías Python
    for lib in ["rich", "InquirerPy", "pyperclip"]:
        if importlib.util.find_spec(lib) is None:
            errores.append(
                f"Falta la librería Python: {lib}. Instala con: pip install {lib}"
            )
    # Tkinter
    try:
        import tkinter
    except ImportError:
        errores.append(
            "Falta la librería tkinter. Instálala según tu sistema operativo."
        )
    if errores:
        console.print("[bold red]Faltan prerequisitos:[/bold red]")
        for e in errores:
            console.print(f"- {e}")
        sys.exit(1)


def main():
    while True:
        proyectos = leer_ssh_config()
        mostrar_proyectos(proyectos)
        alias = preguntar_alias(proyectos)
        repo_url = pedir_repo_url()
        key_path = generar_clave(alias)
        agregar_a_ssh_agent(key_path)
        copiar_clave_publica(key_path)
        destino = seleccionar_carpeta()
        ruta = os.path.join(destino, alias)
        # Actualizar ssh_config ANTES de probar conexión
        actualizar_ssh_config(alias, repo_url, ruta, key_path)
        esperar_confirmacion(repo_url)
        probar_conexion(alias)
        ruta = clonar_repo(alias, repo_url, destino)
        abrir_carpeta(ruta)
        if not inquirer.confirm(
            message="¿Deseas clonar otro proyecto?", default=False
        ).execute():
            console.print("[bold green]¡Hasta luego![/bold green]")
            break


if __name__ == "__main__":
    validar_prerequisitos()
    main()
