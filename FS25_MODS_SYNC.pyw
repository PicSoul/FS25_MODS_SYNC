import os
import requests
import zipfile
import datetime
import filecmp
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog
import json

CONFIG_FILE = "config.json"

def load_config():
    """Load the configuration from a JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"url": "", "mods_folder": ""}

def save_config(url, mods_folder):
    """Save the configuration to a JSON file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"url": url, "mods_folder": mods_folder}, f)

def download_and_extract(url, local_folder, status_label):
    """Download ZIP file from the URL and extract it to the specified local folder."""
    print(f"Downloading ZIP file from {url}...")
    response = requests.get(url)
    zip_file_path = os.path.join(local_folder, "mods.zip")

    with open(zip_file_path, 'wb') as zip_file:
        zip_file.write(response.content)
    print(f"ZIP file downloaded and saved as {zip_file_path}")

    print(f"Extracting contents of {zip_file_path}...")
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            extracted_file_path = os.path.join(local_folder, file_info.filename)

            if os.path.exists(extracted_file_path):
                temp_extracted_file_path = os.path.join(local_folder, "temp_" + file_info.filename)
                zip_ref.extract(file_info, temp_extracted_file_path)

                if os.path.exists(temp_extracted_file_path) and filecmp.cmp(extracted_file_path, temp_extracted_file_path, shallow=False):
                    print(f"File is exactly the same, skipping: {extracted_file_path}")
                    try:
                        os.remove(temp_extracted_file_path)
                    except PermissionError:
                        print(f"Permission denied while trying to remove: {temp_extracted_file_path}")
                    continue

                try:
                    current_time = datetime.datetime(*file_info.date_time)
                except ValueError as e:
                    print(f"Error retrieving date time for {file_info.filename}: {e}")
                    current_time = None

                if current_time:
                    existing_file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(extracted_file_path))

                    if existing_file_mtime < current_time:
                        print(f"Existing file is older, replacing: {extracted_file_path}")
                        os.remove(extracted_file_path)
                        os.rename(temp_extracted_file_path, extracted_file_path)
                    else:
                        print(f"File is up to date: {extracted_file_path}")

                try:
                    os.remove(temp_extracted_file_path)
                except PermissionError:
                    print(f"Permission denied while trying to remove: {temp_extracted_file_path}")

            else:
                print(f"Extracting new file: {extracted_file_path}")
                zip_ref.extract(file_info, local_folder)

    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)
        print(f"Removed the ZIP file: {zip_file_path}")

    print("Cleaning up any temp_ files and folders...")
    for item in os.listdir(local_folder):
        if item.startswith("temp_"):
            item_path = os.path.join(local_folder, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"Removed folder and all contents: {item_path}")
                else:
                    os.remove(item_path)
                    print(f"Removed file: {item_path}")
            except PermissionError:
                print(f"Permission denied while trying to remove: {item_path}")
            except Exception as e:
                print(f"Error removing {item_path}: {e}")

    # Update the status label after syncing
    status_label.config(text="Mods have been synced with the server!")

def start_download(status_label):
    """Start the download process."""
    url = entry_url.get()
    mods_folder = entry_folder.get()

    if not url or not mods_folder:
        messagebox.showwarning("Missing Information", "Please provide both URL and Mods Folder.")
        return

    save_config(url, mods_folder)  # Save the configuration
    download_and_extract(url, mods_folder, status_label)

def select_folder():
    """Open a dialog to select the mods folder."""
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, folder_path)

# Load the configuration if it exists
config = load_config()

# Create the main window
root = tk.Tk()
root.title("Mods Downloader")

# Create and place the URL label and entry
tk.Label(root, text="Mods URL:").grid(row=0, column=0, padx=5, pady=5)
entry_url = tk.Entry(root, width=50)
entry_url.grid(row=0, column=1, padx=5, pady=5)
entry_url.insert(0, config["url"])  # Load saved URL

# Create and place the Mods Folder label and entry
tk.Label(root, text="Mods Folder:").grid(row=1, column=0, padx=5, pady=5)
entry_folder = tk.Entry(root, width=50)
entry_folder.grid(row=1, column=1, padx=5, pady=5)
entry_folder.insert(0, config["mods_folder"])  # Load saved mods folder

# Create and place the Browse button
button_browse = tk.Button(root, text="Browse", command=select_folder)
button_browse.grid(row=1, column=2, padx=5, pady=5)

# Create and place the Download button
button_download = tk.Button(root, text="Download & Extract", command=lambda: start_download(status_label))
button_download.grid(row=2, column=1, padx=5, pady=5)

# Create and place the status label
status_label = tk.Label(root, text="")
status_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

# Start the GUI event loop
root.mainloop()