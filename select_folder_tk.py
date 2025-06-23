try:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    carpeta = filedialog.askdirectory(title='Selecciona carpeta de destino')
    root.destroy()
    if carpeta:
        print(carpeta)  # Solo imprime la ruta
    else:
        print('')  # Imprime vacío si no selecciona nada
except Exception as e:
    print(f'Error al abrir el diálogo de selección de carpeta: {e}')