import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import json
import os
import re
import time



def show_popup(message):
    #This function displays a message in a popup window which can be closed by clicking an "OK" button.
    #Esta función muestra un mensaje en una ventana emergente y se puede cerrar haciendo clic en un botón "OK".
        
    popup = tk.Toplevel()
    popup.title("Message")
    label = tk.Label(popup, text=message, wraplength=250)
    label.pack(fill="x", padx=20, pady=20)
    ok_button = tk.Button(popup, text="OK", command=popup.destroy)
    ok_button.pack(pady=10)

def submit():
    # Get user input from Entry widgets
    # Obtener input del usuario desde los widgets Entry.
    src_url = src_url_entry.get()
    dest_url = dest_url_entry.get()
    src_api_key = src_api_key_entry.get()
    dest_api_key = dest_api_key_entry.get()
    export_path = export_path_entry.get()
    search_replace_pairs = [
        (uid1_src_entry.get(), uid1_dest_entry.get()),
        (uid2_src_entry.get(), uid2_dest_entry.get()),
        (uid3_src_entry.get(), uid3_dest_entry.get()),
        (uid4_src_entry.get(), uid4_dest_entry.get()),
        (uid5_src_entry.get(), uid5_dest_entry.get()),
        (uid6_src_entry.get(), uid6_dest_entry.get())  
    ]
    # Success or error popup
    success = main(src_url, dest_url, src_api_key, dest_api_key, export_path, search_replace_pairs)
    if success:
        show_popup("All dashboards have been successfully exported to the destination Grafana.")
    else:
        show_popup("An error occurred during the dashboard export process. Check the console for details.")

    
def main(src_url, dest_url, src_api_key, dest_api_key, export_path, search_replace_pairs):
    try:
        def replace_id_with_null(file_path):
            """
            Replaces the 'id' property with null in the specified JSON file.

            Args:
                file_path (str): The path to the JSON file.
            """
            """
            Reemplaza la propiedad 'id' con null en el archivo JSON especificado.

            Args:
                file_path (str): La ruta al archivo JSON.
            """
            with open(file_path, "r") as f:
                content = f.read()
            content = re.sub(r'"id": \d+,', '"id": null,', content)

            # Handle the numeric panel ID case
            # Manejar ID del panel numérico
            content = re.sub(r'"panelId": \d+,', '"panelId": null,', content)

            with open(file_path, "w") as f:
                f.write(content)

        def replace_first_id_with_null(file_path):
            """
            Replaces the first 'id' property with null in the specified JSON file.

            Args:
                file_path (str): The path to the JSON file.
            """
            """
            Reemplaza la primera propiedad 'id' con null en el archivo JSON especificado.

            Args:
                file_path (str): La ruta al archivo JSON.
            """
            with open(file_path, "r") as f:
                content = f.read()

            # Use a flag to ensure that only the first 'id' parameter is replaced
            # Usar un indicador para asegurar que solo se reemplace el primer parámetro 'id'
            first_id_replaced = False

            # This function will be called for each match found by re.sub
            # Esta función se llamará para cada coincidencia encontrada por re.sub
            def replace_first_id(match):
                nonlocal first_id_replaced
                if not first_id_replaced:
                    first_id_replaced = True
                    return '"id": null,'
                return match.group(0)

            content = re.sub(r'"id": \d+,', replace_first_id, content)

            with open(file_path, "w") as f:
                f.write(content)

        def replace_uid_pairs(file_path, search_replace_pairs):
            """
            Replaces specified UID pairs in the JSON file.

            Args:
                file_path (str): The path to the JSON file.
                search_replace_pairs (List[Tuple[str, str]]): A list of tuples containing search and replace strings.
            """
            """
            Reemplaza los pares UID especificados en el archivo JSON.

            Args:
                file_path (str): La ruta al archivo JSON.
                search_replace_pairs (List[Tuple[str, str]]): Una lista de tuplas que contienen cadenas de búsqueda y reemplazo.
            """
            with open(file_path, "r") as f:
                content = f.read()

            for search, replace in search_replace_pairs:
                content = content.replace(search, replace)

            with open(file_path, "w") as f:
                f.write(content)




        def import_dashboard(dashboard_data, folder_id):
            import_url = f'{dest_url}/api/dashboards/import'
            headers = {
                'Authorization': f'Bearer {dest_api_key}',
                'Content-Type': 'application/json'
            }
            data = {'dashboard': dashboard_data, 'overwrite': True}
            if folder_id is not None:
                data['folderId'] = folder_id

            formatted_data = json.dumps(data, indent=4)
            response = requests.post(import_url, headers=headers, data=formatted_data)

            if response.status_code != 200:
                try:
                    error_message = json.loads(response.text).get("message")
                    if "alert validation error" in error_message:
                        return None, error_message
                    else:
                        return None, response.text
                except Exception as e:
                    return None, str(e)

            return response, None
        




        # Get a list of all the folders in the source Grafana instance
        # Obtener una lista de todas las carpetas en la instancia de Grafana de origen
        src_folders_url = f'{src_url}/api/folders'
        src_folders_resp = requests.get(src_folders_url, headers={'Authorization': f'Bearer {src_api_key}'})
        src_folders = json.loads(src_folders_resp.content)


        # Get a list of all the dashboards in the source Grafana instance
        # Obtener una lista de todos los dashboard en la instancia de Grafana de origen
        src_all_dashboards_url = f'{src_url}/api/search?type=dash-db'
        src_all_dashboards_resp = requests.get(src_all_dashboards_url, headers={'Authorization': f'Bearer {src_api_key}'})
        src_all_dashboards = json.loads(src_all_dashboards_resp.content)

        # Print folder IDs of all dashboards
        # Imprime en consola los IDs de carpeta de todos los dashboards
        print("Folder IDs of all dashboards:")
        for d in src_all_dashboards:
            if isinstance(d, dict):
                print(f"{d['title']}: {d.get('folderId')}")
            else:
                print(f"Unexpected item in src_all_dashboards: {d}")

        # Get dashboards in the General folder (folderId is 0)
        # Obtener dashboards en la carpeta General (folderId es 0)
        general_folder_dashboards = [d for d in src_all_dashboards if d.get("folderId") == 0]

        for folder in src_folders + [{"title": "General", "id": 0}]:  # Add "General" folder manually
            print(f'Processing folder: {folder.get("title")}')
            folder_id = folder.get("id")

            # Filter dashboards by their folder ID
            # Filtrar los dashboard por su ID de carpeta
            if folder_id == 0:  # Modify the condition to include dashboards from the General folder # Modificar la condición para incluir los dashboards de la carpeta General
                folder_dashboards = [d for d in src_all_dashboards if d.get("folderId") == 0 or d.get("folderId") is None]
            else:
                folder_dashboards = [d for d in src_all_dashboards if d.get("folderId") == folder_id]

            print(f'Dashboards found in the folder: {len(folder_dashboards)}')

            if folder["title"] != "General":
                # Create a folder in the destination Grafana instance
                # Crear una carpeta en la instancia de Grafana de destino
                folder_title = folder.get('title')
                folder_uid = folder.get('uid')
                folder_url = f'{dest_url}/api/folders'
                folder_data = {'title': folder_title, 'uid': folder_uid}
                dest_folder_resp = requests.post(folder_url, headers={'Authorization': f'Bearer {dest_api_key}'}, json=folder_data)
                dest_folder_id = dest_folder_resp.json().get('id')
                
                # Initialize the folder_id_map dictionary
                folder_id_map = {}
            
                # Add folder ID mapping
                # Agregar asignación de ID de carpeta
                folder_id_map[folder_id] = dest_folder_id
            else:
                dest_folder_id = 0
            
            # Get a list of all the dashboards in the folder
            # Obtener una lista de todos los dashboard en la carpeta
            src_dashboards_url = f'{src_url}/api/search?query=&folderUid={folder_uid}&type=dash-db'
            src_dashboards_resp = requests.get(src_dashboards_url, headers={'Authorization': f'Bearer {src_api_key}'})
            src_dashboards = json.loads(src_dashboards_resp.content)

            # Export each dashboard and save it to a file
            # Exportar cada dashboard y guardarlo en un archivo
            for dashboard in folder_dashboards:
                print(f'Processing dashboard: {dashboard["title"]}')
                dashboard_url = f'{src_url}/api/dashboards/uid/{dashboard["uid"]}'  # Use `dashboard["uid"]` instead of `dashboard_uid`# Usar `dashboard["uid"]` en lugar de `dashboard_uid`
                dashboard_resp = requests.get(dashboard_url, headers={'Authorization': f'Bearer {src_api_key}'})
                dashboard_data = json.loads(dashboard_resp.content)['dashboard']
                dashboard_title = dashboard_data['title'].replace('/', '_')  # Replace forward slashes with underscores # Reemplazar barras inclinadas con guiones bajos
                folder_path = os.path.join(export_path, folder_title)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                export_file = os.path.join(folder_path, f'{dashboard_title}.json')

                # Write the dashboard data to the file
                # Escribir los datos del dashboard en el archivo
                with open(export_file, 'w') as f:
                    json.dump(dashboard_data, f, indent=4)

                # First attempt: Import the dashboard with modified IDs
                # Primer intento: importar el dashboard con IDs modificados
                replace_uid_pairs(export_file, search_replace_pairs)
                replace_id_with_null(export_file)
                with open(export_file, 'r') as f:
                    dashboard_data_modified = json.load(f)

                try:
                    mapped_dest_folder_id = folder_id_map.get(folder_id, 0)  # Get the destination folder ID from the mapping, default to 0
                    response, error_message = import_dashboard(dashboard_data_modified, mapped_dest_folder_id)
                    if response is not None:
                        print(f'Successfully imported {dashboard_title} ')
                    else:
                        print(f'Failed to import {dashboard_title}: {error_message}')


                except Exception as e:
                    print(f'Failed to import {dashboard_title}: {str(e)}')



                    # Second attempt: Import the dashboard without modifying IDs
                    # Reload the original dashboard data from the file
                    # Segundo intento: importar el dashboard sin modificar los IDs
                    # Volver a cargar los datos originales del dashboard desde el archivo
                    with open(export_file, 'r') as f:
                        dashboard_data = json.load(f)

                    # Replace UIDs for the second attempt
                    # Reemplazar los UIDs para el segundo intento
                    replace_uid_pairs(export_file, search_replace_pairs)

                    # Replace only the first 'id' parameter with null for the second attempt
                    # Reemplazar solo el primer parámetro 'id' con nulo para el segundo intento
                    replace_first_id_with_null(export_file)

                    try:
                        mapped_dest_folder_id = folder_id_map.get(folder_id, 0)  # Get the destination folder ID from the mapping, default to 0 # Obtener el ID de carpeta de destino del mapeo, predeterminado a 0
                        response, error_message = import_dashboard(dashboard_data, mapped_dest_folder_id)
                        if response is not None:
                            print(f'Successfully imported {dashboard_title} without modifying IDs')
                        else:
                            print(f'Failed to import {dashboard_title} without modifying IDs: {error_message}')
                    finally:
                        time.sleep(2)  # Add a delay between requests # Agregar una pausa entre las solicitudes
        # If no errors occurred, return True
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        # If an error occurred, return False
        return False

root = tk.Tk()
root.title("Grafana Dashboard Migrator")

# Create labels and entry widgets for user input
# Crear etiquetas y widgets de entrada para el input del usuario.
src_url_label = tk.Label(root, text="Source URL:")
src_url_entry = tk.Entry(root, width=50)
dest_url_label = tk.Label(root, text="Destination URL:")
dest_url_entry = tk.Entry(root, width=50)
src_api_key_label = tk.Label(root, text="Source API Key:")
src_api_key_entry = tk.Entry(root, width=50)
dest_api_key_label = tk.Label(root, text="Destination API Key:")
dest_api_key_entry = tk.Entry(root, width=50)

def browse_export_path():
    export_path_entry.delete(0, tk.END)
    export_path_entry.insert(0, filedialog.askdirectory())

export_path_label = tk.Label(root, text="Export Path:")
export_path_entry = tk.Entry(root, width=50)
export_path_button = tk.Button(root, text="Browse", command=browse_export_path)

search_replace_label = tk.Label(root, text="Replace Datasource UIDs (Source/Destination)")
uid1_src_entry = tk.Entry(root, width=20)
uid1_dest_entry = tk.Entry(root, width=20)
uid2_src_entry = tk.Entry(root, width=20)
uid2_dest_entry = tk.Entry(root, width=20)
uid3_src_entry = tk.Entry(root, width=20)
uid3_dest_entry = tk.Entry(root, width=20)
uid4_src_entry = tk.Entry(root, width=20)
uid4_dest_entry = tk.Entry(root, width=20)
uid5_src_entry = tk.Entry(root, width=20)
uid5_dest_entry = tk.Entry(root, width=20)
uid6_src_entry = tk.Entry(root, width=20)
uid6_dest_entry = tk.Entry(root, width=20)


submit_button = tk.Button(root, text="Submit", command=submit)

# Position the widgets on the grid
# Posicionar los widgets en la cuadricula

src_url_label.grid(row=0, column=0)
src_url_entry.grid(row=0, column=1)
dest_url_label.grid(row=1, column=0)
dest_url_entry.grid(row=1, column=1)
src_api_key_label.grid(row=2, column=0)
src_api_key_entry.grid(row=2, column=1)
dest_api_key_label.grid(row=3, column=0)
dest_api_key_entry.grid(row=3, column=1)
export_path_label.grid(row=4, column=0)
export_path_entry.grid(row=4, column=1)
export_path_button.grid(row=4, column=2, padx=5)
search_replace_label.grid(row=5, column=0, pady=10)
uid1_src_entry.grid(row=6, column=0)
uid1_dest_entry.grid(row=6, column=1)
uid2_src_entry.grid(row=7, column=0)
uid2_dest_entry.grid(row=7, column=1)
uid3_src_entry.grid(row=8, column=0)
uid3_dest_entry.grid(row=8, column=1)
uid4_src_entry.grid(row=9, column=0)
uid4_dest_entry.grid(row=9, column=1)
uid5_src_entry.grid(row=10, column=0)
uid5_dest_entry.grid(row=10, column=1)
uid6_src_entry.grid(row=11, column=0)
uid6_dest_entry.grid(row=11, column=1)
submit_button.grid(row=12, column=1, pady=10)

root.mainloop()
