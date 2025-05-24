import shutil
import tempfile
import zipfile
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import psutil

# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_drive_letters():
    return [
        p.device
        for p in psutil.disk_partitions()
        if 'cdrom' not in p.opts.lower() and p.fstype
    ]

def move_items(sources, destination, log_widget=None):
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    for src in sources:
        src = Path(src)
        if not src.exists():
            if log_widget:
                log_widget.insert(tk.END, f"[Warn] {src} missing\n")
            continue
        tgt = dest / src.name
        try:
            shutil.move(str(src), str(tgt))
            if log_widget:
                log_widget.insert(tk.END, f"[OK] Moved {src.name}\n")
        except Exception as e:
            traceback.print_exc()
            if log_widget:
                log_widget.insert(tk.END, f"[Error] {e}\n")

def unzip_if_needed(path, log_widget=None):
    path = Path(path)
    if path.suffix.lower() == '.zip':
        tempdir = Path(tempfile.mkdtemp(prefix='unzipped_'))
        if log_widget:
            log_widget.insert(tk.END, f"[OK] Unzipping to {tempdir}\n")
        with zipfile.ZipFile(path, 'r') as zf:
            zf.extractall(tempdir)
        return tempdir
    return path

def delete_moved(delete_button, log_widget, root):
    folder = getattr(delete_button, 'folder', None)
    if folder and Path(folder).exists():
        if messagebox.askyesno("Confirm Delete", f"Delete moved folder {folder}?"):
            try:
                shutil.rmtree(folder)
                log_widget.insert(tk.END, "[OK] Deleted moved folder\n")
                delete_button.config(state=tk.DISABLED)
            except Exception as e:
                traceback.print_exc()
                messagebox.showerror("Error", str(e))
    else:
        messagebox.showinfo("Info", "Nothing to delete")

# ─── Core Operation ──────────────────────────────────────────────────────────

def perform_operation(source, folder_name, destination, drive, log_widget, delete_button, _):
    try:
        log_widget.delete(1.0, tk.END)
        src = Path(source)
        if not src.exists():
            messagebox.showerror("Error", f"{src} not found")
            return

        target = Path(destination) if destination else Path(drive) / folder_name
        target.mkdir(parents=True, exist_ok=True)

        actual = unzip_if_needed(src, log_widget)
        items = list(actual.iterdir())
        if items:
            move_items(items, target, log_widget)
        else:
            log_widget.insert(tk.END, "[Info] Nothing to move\n")

        if actual != src and actual.exists():
            shutil.rmtree(actual)
            log_widget.insert(tk.END, "[OK] Removed temp folder\n")

        log_widget.insert(tk.END, "[Done] Operation completed\n")
        messagebox.showinfo("Done", "All operations completed successfully.")
        delete_button.config(state=tk.NORMAL)
        delete_button.folder = target

        # **DO NOT** close here—user must click “Leave” to exit

    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Error", str(e))
        # **DO NOT** close here either

# ─── GUI Helpers ────────────────────────────────────────────────────────────

def browse_file(entry_widget):
    path = filedialog.askopenfilename(filetypes=[("All Files","*.*")])
    if path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)

def browse_directory(entry_widget):
    path = filedialog.askdirectory()
    if path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)

# ─── GUI Layout ─────────────────────────────────────────────────────────────

def create_gui():
    root = tk.Tk()
    root.title("Move & Unzip Utility")
    root.geometry("600x600")

    frm = tk.Frame(root)
    frm.pack(padx=10, pady=10, fill=tk.X)

    # Source
    tk.Label(frm, text="Source (folder or .zip):").grid(row=0, column=0, sticky='w')
    src_e = tk.Entry(frm); src_e.grid(row=0, column=1, sticky='ew')
    tk.Button(frm, text="Browse", command=lambda: browse_file(src_e)).grid(row=0, column=2)

    # New folder name
    tk.Label(frm, text="New Folder Name:").grid(row=1, column=0, sticky='w')
    name_e = tk.Entry(frm); name_e.grid(row=1, column=1, sticky='ew')
    name_e.insert(0, "New Folder")

    # Optional destination
    tk.Label(frm, text="Destination (optional):").grid(row=2, column=0, sticky='w')
    dest_e = tk.Entry(frm); dest_e.grid(row=2, column=1, sticky='ew')
    tk.Button(frm, text="Browse", command=lambda: browse_directory(dest_e)).grid(row=2, column=2)

    # Drive fallback
    drives = get_drive_letters()
    default = 'D:\\' if 'D:\\' in drives else (drives[0] if drives else 'C:\\')
    tk.Label(frm, text="Drive (if no dest):").grid(row=3, column=0, sticky='w')
    drive_var = tk.StringVar(value=default)
    drive_cb = ttk.Combobox(frm, textvariable=drive_var, values=drives, state='readonly')
    drive_cb.grid(row=3, column=1, sticky='ew')

    frm.columnconfigure(1, weight=1)

    # Log area
    log = scrolledtext.ScrolledText(root, height=18)
    log.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)

    # Buttons: Run, Delete Moved, Leave
    btn_fr = tk.Frame(root); btn_fr.pack(pady=(0,10))
    run_b = tk.Button(btn_fr, text="Run")
    run_b.grid(row=0, column=0, padx=5)
    del_b = tk.Button(btn_fr, text="Delete Moved", state=tk.DISABLED,
                      command=lambda: delete_moved(del_b, log, root))
    del_b.grid(row=0, column=1, padx=5)
    leave_b = tk.Button(btn_fr, text="Leave", command=root.destroy)
    leave_b.grid(row=0, column=2, padx=5)

    run_b.config(command=lambda: perform_operation(
        src_e.get(), name_e.get(), dest_e.get().strip(),
        drive_var.get(), log, del_b, root
    ))

    root.mainloop()

if __name__ == "__main__":
    create_gui()
