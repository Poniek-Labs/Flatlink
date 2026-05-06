import tkinter as tk
from tkinter import messagebox
import subprocess
import re
import threading
import os
import sys

def extract_app_id(flathub_url):
    match = re.search(r'flathub\.org/apps/([\w\.\-]+)', flathub_url)
    if match:
        return match.group(1)
    return None

def do_install(app_id):
    cmd = ["flatpak", "install", "-y", "flathub", app_id]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        root.after(0, lambda: messagebox.showinfo("Success", f"Installed {app_id} successfully!\n\n{output}"))
    except subprocess.CalledProcessError as e:
        root.after(0, lambda: messagebox.showerror("Install Failed", f"Failed to install {app_id}.\n\n{e.output}"))
    finally:
        root.after(0, hide_loading)

def install_app():
    url = entry.get().strip()
    app_id = extract_app_id(url)
    if not app_id:
        messagebox.showerror("Error", "Invalid Flathub URL.")
        return
    show_loading()
    threading.Thread(target=do_install, args=(app_id,), daemon=True).start()

def show_loading():
    loading_label.config(text="Installing, please wait...")
    loading_label.place(relx=0.5, rely=0.7, anchor=tk.CENTER)

def hide_loading():
    loading_label.place_forget()

root = tk.Tk()
root.title("Flatlink - Flathub App Installer")

tk.Label(root, text="Paste Flathub App Link:").pack(pady=8)
entry = tk.Entry(root, width=50, font=("Arial", 12))
entry.pack(padx=15, pady=5)

install_btn = tk.Button(root, text="Install", command=install_app, font=("Arial", 12, "bold"), bg="#4caf50", fg="white")
install_btn.pack(pady=15)

# Instead of GIF, just a text label for loading
loading_label = tk.Label(root, text="", font=("Arial", 11, "italic"), fg="grey")

root.mainloop()

""" Made Erik W for Poniek Labs
    Do not clone, modify or redistribute """
