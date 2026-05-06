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
    Do not clone, modify or redistribute """"""
Flatlink v1.2 — Poniek Labs
Made by Erik W for Poniek Labs
Do not clone, modify or redistribute
"""

import tkinter as tk
from tkinter import font as tkfont
import subprocess
import re
import threading
import math

# ── Palette ──────────────────────────────────────────────────────────────────
BG          = "#0f1117"
SURFACE     = "#1a1d27"
SURFACE2    = "#222636"
ACCENT      = "#5b8dee"
ACCENT2     = "#7c6af7"
SUCCESS     = "#3ecf8e"
ERROR_COL   = "#f87171"
TEXT        = "#e8eaf6"
MUTED       = "#6b7280"
BORDER      = "#2d3148"

# ── URL / App-ID extraction ───────────────────────────────────────────────────
def extract_app_id(raw: str) -> str | None:
    raw = raw.strip()

    # Pattern 1 – any path segment that looks like a reverse-domain app ID
    # e.g. /apps/org.chromium.Chromium  OR  /en/apps/org.chromium.Chromium
    match = re.search(r'/apps/([\w][\w.\-]+)', raw)
    if match:
        candidate = match.group(1)
        # Must contain at least one dot to be a valid reverse-domain ID
        if '.' in candidate:
            return candidate

    # Pattern 2 – bare app ID typed directly (e.g. "org.chromium.Chromium")
    bare = re.match(r'^([\w][\w.\-]+)$', raw)
    if bare and '.' in bare.group(1):
        return bare.group(1)

    return None


# ── Main application ──────────────────────────────────────────────────────────
class FlatLinkApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Flatlink")
        self.root.geometry("520x560")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # Animation state
        self._anim_angle   = 0.0
        self._anim_dots    = 0
        self._anim_id      = None
        self._progress_val = 0.0
        self._installing   = False

        self._build_fonts()
        self._build_ui()

    # ── Fonts ─────────────────────────────────────────────────────────────────
    def _build_fonts(self):
        self.f_logo    = tkfont.Font(family="DejaVu Sans", size=22, weight="bold")
        self.f_tagline = tkfont.Font(family="DejaVu Sans", size=9)
        self.f_label   = tkfont.Font(family="DejaVu Sans", size=10)
        self.f_entry   = tkfont.Font(family="DejaVu Sans Mono", size=10)
        self.f_btn     = tkfont.Font(family="DejaVu Sans", size=11, weight="bold")
        self.f_status  = tkfont.Font(family="DejaVu Sans", size=9, slant="italic")
        self.f_version = tkfont.Font(family="DejaVu Sans", size=8)

    # ── UI layout ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Logo / header ──────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=BG)
        header.pack(pady=(32, 0))

        # Logo canvas — animated hexagon mark
        self.logo_canvas = tk.Canvas(
            header, width=72, height=72, bg=BG,
            highlightthickness=0
        )
        self.logo_canvas.pack()
        self._draw_logo()

        tk.Label(
            header, text="Flatlink", font=self.f_logo,
            fg=TEXT, bg=BG
        ).pack(pady=(10, 0))

        tk.Label(
            header, text="Flathub app installer for Linux",
            font=self.f_tagline, fg=MUTED, bg=BG
        ).pack()

        # ── Divider ────────────────────────────────────────────────────────
        tk.Canvas(
            self.root, height=1, bg=BORDER, highlightthickness=0
        ).pack(fill="x", padx=40, pady=20)

        # ── URL entry ──────────────────────────────────────────────────────
        tk.Label(
            self.root,
            text="Paste a Flathub app URL or App ID:",
            font=self.f_label, fg=MUTED, bg=BG, anchor="w"
        ).pack(padx=48, anchor="w")

        entry_frame = tk.Frame(self.root, bg=ACCENT, padx=2, pady=2)
        entry_frame.pack(padx=46, pady=(6, 0), fill="x")

        inner = tk.Frame(entry_frame, bg=SURFACE)
        inner.pack(fill="x")

        self.entry = tk.Entry(
            inner, font=self.f_entry,
            bg=SURFACE, fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=8
        )
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", lambda _: self._start_install())
        self.entry.bind("<FocusIn>",  lambda _: entry_frame.config(bg=ACCENT))
        self.entry.bind("<FocusOut>", lambda _: entry_frame.config(bg=BORDER))
        entry_frame.config(bg=BORDER)

        tk.Label(
            self.root,
            text="e.g. https://flathub.org/apps/org.chromium.Chromium",
            font=self.f_version, fg=MUTED, bg=BG
        ).pack(padx=48, anchor="w", pady=(4, 0))

        # ── Install button ─────────────────────────────────────────────────
        self.btn = tk.Button(
            self.root, text="Install App",
            font=self.f_btn,
            bg=ACCENT, fg="white", activebackground=ACCENT2,
            activeforeground="white",
            relief="flat", bd=0, padx=0, pady=12,
            cursor="hand2",
            command=self._start_install
        )
        self.btn.pack(padx=46, pady=20, fill="x")
        self.btn.bind("<Enter>", lambda _: self.btn.config(bg=ACCENT2))
        self.btn.bind("<Leave>", lambda _: self.btn.config(
            bg=ACCENT if not self._installing else SURFACE2))

        # ── Progress area ──────────────────────────────────────────────────
        self.progress_frame = tk.Frame(self.root, bg=BG)
        self.progress_frame.pack(padx=46, fill="x")

        # Track background
        self.track = tk.Canvas(
            self.progress_frame, height=6, bg=SURFACE2,
            highlightthickness=0
        )
        self.track.pack(fill="x")

        # Animated progress bar drawn on a second canvas overlaid
        self.prog_canvas = tk.Canvas(
            self.progress_frame, height=6, bg=BG,
            highlightthickness=0
        )
        # (placed dynamically when installing)

        # Status label
        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(
            self.progress_frame,
            textvariable=self.status_var,
            font=self.f_status, fg=MUTED, bg=BG
        )
        self.status_lbl.pack(pady=(6, 0))

        # ── Spinner canvas ─────────────────────────────────────────────────
        self.spinner_canvas = tk.Canvas(
            self.root, width=40, height=40, bg=BG,
            highlightthickness=0
        )
        # (placed dynamically)

        # ── Footer ─────────────────────────────────────────────────────────
        tk.Label(
            self.root,
            text="v1.2  ·  Poniek Labs",
            font=self.f_version, fg=MUTED, bg=BG
        ).pack(side="bottom", pady=12)

    # ── Logo drawing ──────────────────────────────────────────────────────────
    def _draw_logo(self, angle: float = 0.0):
        c = self.logo_canvas
        c.delete("all")
        cx, cy, r = 36, 36, 28

        # Outer hexagon (rotated)
        pts = []
        for i in range(6):
            a = math.radians(60 * i + angle)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
        c.create_polygon(pts, outline=ACCENT, fill=SURFACE2, width=2.5)

        # Inner hexagon (counter-rotated)
        pts2 = []
        for i in range(6):
            a = math.radians(60 * i - angle + 30)
            pts2 += [cx + (r * 0.55) * math.cos(a),
                     cy + (r * 0.55) * math.sin(a)]
        c.create_polygon(pts2, outline=ACCENT2, fill=SURFACE, width=1.5)

        # Down-arrow symbol in centre
        aw = 9
        c.create_line(cx, cy - 10, cx, cy + 7,
                      fill=TEXT, width=2.5, capstyle="round")
        c.create_line(cx - aw, cy - 1, cx, cy + 9,
                      fill=TEXT, width=2.5, capstyle="round")
        c.create_line(cx + aw, cy - 1, cx, cy + 9,
                      fill=TEXT, width=2.5, capstyle="round")

    # ── Spinner ───────────────────────────────────────────────────────────────
    def _draw_spinner(self, angle: float):
        c = self.spinner_canvas
        c.delete("all")
        cx, cy, r = 20, 20, 13
        for i in range(8):
            a = math.radians(45 * i + angle)
            x1 = cx + (r - 5) * math.cos(a)
            y1 = cy + (r - 5) * math.sin(a)
            x2 = cx + r * math.cos(a)
            y2 = cy + r * math.sin(a)
            alpha = int(255 * (i + 1) / 8)
            grey = int(91 + (141 - 91) * (i / 7))
            colour = f"#{ACCENT[1:3]}{ACCENT[3:5]}{ACCENT[5:7]}"
            # Fade dots
            fade_colours = [
                "#182240", "#1e2c55", "#253668", "#2d4280",
                "#3a5299", "#4a68b8", "#5278d0", ACCENT
            ]
            c.create_line(x1, y1, x2, y2,
                          fill=fade_colours[i], width=2.5,
                          capstyle="round")

    # ── Animated progress bar ─────────────────────────────────────────────────
    def _draw_progress(self, frac: float):
        c = self.prog_canvas
        c.delete("all")
        w = c.winfo_width() or 428
        filled = int(w * min(frac, 1.0))
        if filled > 0:
            # Gradient-ish bar using two overlapping rectangles
            c.create_rectangle(0, 0, filled, 6, fill=ACCENT2, outline="")
            c.create_rectangle(0, 0, int(filled * 0.6), 6, fill=ACCENT, outline="")

    # ── Animation loop ────────────────────────────────────────────────────────
    def _animate(self):
        if not self._installing:
            return

        self._anim_angle  = (self._anim_angle + 6) % 360
        self._anim_dots   = (self._anim_dots + 1) % 4
        self._progress_val = min(self._progress_val + 0.004, 0.92)

        self._draw_logo(self._anim_angle * 0.15)
        self._draw_spinner(self._anim_angle)
        self._draw_progress(self._progress_val)

        dots = "." * self._anim_dots
        self.status_var.set(f"Installing{dots}  (this may take a minute)")

        self._anim_id = self.root.after(40, self._animate)

    # ── Install flow ──────────────────────────────────────────────────────────
    def _start_install(self):
        if self._installing:
            return

        raw    = self.entry.get().strip()
        app_id = extract_app_id(raw)

        if not app_id:
            self._flash_error(
                "Invalid URL or App ID.\n\n"
                "Paste a full Flathub URL (e.g. https://flathub.org/apps/org.chromium.Chromium)\n"
                "or type an App ID directly (e.g. org.chromium.Chromium)."
            )
            return

        self._installing   = True
        self._progress_val = 0.0

        self.btn.config(
            state="disabled", text="Installing…",
            bg=SURFACE2, fg=MUTED
        )

        # Show progress widgets
        self.prog_canvas.place(x=0, y=0, relwidth=1.0, height=6,
                               in_=self.track)
        self.spinner_canvas.pack(pady=(10, 0))
        self._animate()

        threading.Thread(
            target=self._do_install, args=(app_id,), daemon=True
        ).start()

    def _do_install(self, app_id: str):
        cmd = ["flatpak", "install", "-y", "flathub", app_id]
        try:
            output = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, universal_newlines=True
            )
            self.root.after(0, lambda: self._on_success(app_id, output))
        except subprocess.CalledProcessError as e:
            self.root.after(0, lambda: self._on_error(app_id, e.output))

    def _on_success(self, app_id: str, output: str):
        self._stop_animation(success=True)
        self._draw_logo(0)

        # Green confirmation bar
        self._progress_val = 1.0
        self.prog_canvas.delete("all")
        w = self.track.winfo_width() or 428
        self.prog_canvas.create_rectangle(0, 0, w, 6, fill=SUCCESS, outline="")

        self.status_var.set(f"✓  {app_id} installed successfully!")
        self.status_lbl.config(fg=SUCCESS)

        self._show_result_popup("✓ Installed!", f"{app_id} was installed successfully.", ok=True)

    def _on_error(self, app_id: str, output: str):
        self._stop_animation(success=False)
        self._draw_logo(0)

        self.prog_canvas.delete("all")
        w = self.track.winfo_width() or 428
        self.prog_canvas.create_rectangle(0, 0, w, 6, fill=ERROR_COL, outline="")

        self.status_var.set("✗  Installation failed.")
        self.status_lbl.config(fg=ERROR_COL)

        self._show_result_popup("Installation Failed",
            f"Could not install {app_id}.\n\n{output[:400]}", ok=False)

    def _stop_animation(self, success: bool):
        self._installing = False
        if self._anim_id:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None
        self.spinner_canvas.pack_forget()
        self.btn.config(
            state="normal", text="Install App",
            bg=ACCENT, fg="white"
        )

    # ── Popups ────────────────────────────────────────────────────────────────
    def _show_result_popup(self, title: str, msg: str, ok: bool):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        colour = SUCCESS if ok else ERROR_COL
        icon   = "✓" if ok else "✗"

        tk.Label(win, text=icon, font=tkfont.Font(size=28, weight="bold"),
                 fg=colour, bg=BG).pack(pady=(24, 4))
        tk.Label(win, text=title,
                 font=tkfont.Font(family="DejaVu Sans", size=13, weight="bold"),
                 fg=TEXT, bg=BG).pack()
        tk.Label(win, text=msg,
                 font=tkfont.Font(family="DejaVu Sans", size=9),
                 fg=MUTED, bg=BG, wraplength=340, justify="center").pack(
                     padx=30, pady=(8, 20))

        tk.Button(
            win, text="OK",
            font=tkfont.Font(family="DejaVu Sans", size=10, weight="bold"),
            bg=colour, fg="white", relief="flat", bd=0,
            padx=40, pady=8, cursor="hand2",
            command=win.destroy
        ).pack(pady=(0, 24))

    def _flash_error(self, msg: str):
        win = tk.Toplevel(self.root)
        win.title("Error")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="✗", font=tkfont.Font(size=24, weight="bold"),
                 fg=ERROR_COL, bg=BG).pack(pady=(20, 4))
        tk.Label(win, text=msg,
                 font=tkfont.Font(family="DejaVu Sans", size=9),
                 fg=MUTED, bg=BG, wraplength=340, justify="center").pack(
                     padx=30, pady=(4, 16))
        tk.Button(
            win, text="OK",
            font=tkfont.Font(family="DejaVu Sans", size=10, weight="bold"),
            bg=ERROR_COL, fg="white", relief="flat", bd=0,
            padx=40, pady=8, cursor="hand2",
            command=win.destroy
        ).pack(pady=(0, 20))


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = FlatLinkApp(root)
    root.mainloop()
