"""The launcher window: a synthwave start centre for Writer, Calc, Impress and the PDF tools.

Plain Tk widgets are used (not ttk) so the neon colours look the same on Windows and Linux.
Long PDF and conversion jobs run in a worker thread; their outcome comes back through ``after``.
The interface language can be switched at any time from the Language menu; it also sets
LibreOffice's interface language for the next start.
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
import traceback
import webbrowser
from pathlib import Path
from tkinter import filedialog, font, messagebox, simpledialog

from . import __version__, config, i18n, libreoffice, pdftools
from .paths import GUIDE, ICON_PNG

# Synthwave palette (the same colours as the README badges and the banner).
BG = "#12002b"
PANEL = "#1f0a45"
PINK = "#ff2975"
CYAN = "#2de2e6"
YELLOW = "#ffd640"
PURPLE = "#b026ff"
TEXT = "#f6e9ff"
MUTED = "#a58fc7"
HEADER_H = 150
WIDTH = 760

t = i18n.t


def open_path(path: Path) -> None:
    """Open a file or folder with the system's default application."""
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606 - user-chosen local path
    else:
        subprocess.Popen(["xdg-open", str(path)], start_new_session=True)


def _family(root: tk.Misc, *choices: str) -> str:
    available = set(font.families(root))
    return next((c for c in choices if c in available), "TkDefaultFont")


class App:
    """The launcher. ``root`` is the Tk window; nothing is shown until ``root.mainloop()``."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.lang = i18n.get_language()
        self.inst = libreoffice.find()
        self.lo_version = self.inst.version() if self.inst else None
        self.title_family = _family(root, "Bahnschrift", "Segoe UI Black", "DejaVu Sans", "Liberation Sans")
        self.body_family = _family(root, "Segoe UI", "DejaVu Sans", "Liberation Sans")
        root.title("Riot Office")
        root.configure(bg=BG)
        root.resizable(False, False)
        if ICON_PNG.exists():
            self._icon = tk.PhotoImage(file=str(ICON_PNG))
            root.iconphoto(True, self._icon)
        self.lang_var = tk.StringVar(value=self.lang)
        self.status_var = tk.StringVar()
        self.body = None
        self.build()

    # ----- layout -------------------------------------------------------------------------
    def build(self) -> None:
        """(Re)build every widget in the current language."""
        if self.body is not None:
            self.body.destroy()
        self._menu()
        self.body = tk.Frame(self.root, bg=BG)
        self.body.pack(fill="both", expand=True)
        # The status line is packed first, so that the window always leaves room for it.
        self.status = tk.Label(self.body, textvariable=self.status_var, bg=PANEL, fg=MUTED, anchor="w",
                               padx=12, pady=6, font=(self.body_family, 9))
        self.status.pack(fill="x", side="bottom")
        self._header(self.body)

        apps = tk.Frame(self.body, bg=BG)
        apps.pack(padx=24, pady=(18, 8), fill="x")
        for column, (module, colour) in enumerate((("writer", CYAN), ("calc", YELLOW), ("impress", PINK))):
            self._app_card(apps, module, colour).grid(row=0, column=column, padx=8, sticky="nsew")
            apps.columnconfigure(column, weight=1, uniform="apps")

        self._button(self.body, t("open_file", self.lang), self.on_open_file, PURPLE).pack(pady=(6, 14))

        tk.Label(self.body, text=t("pdf_tools", self.lang).upper(), bg=BG, fg=PINK,
                 font=(self.title_family, 12, "bold")).pack(anchor="w", padx=32)
        tools = tk.Frame(self.body, bg=BG)
        tools.pack(padx=24, pady=(4, 12), fill="x")
        actions = [("pdf_merge", self.on_merge), ("pdf_split", self.on_split), ("pdf_rotate", self.on_rotate),
                   ("pdf_convert", self.on_convert), ("pdf_ocr", self.on_ocr)]
        for i, (key, handler) in enumerate(actions):
            button = self._button(tools, t(key, self.lang), handler, CYAN, small=True)
            button.grid(row=i // 3, column=i % 3, padx=6, pady=4, sticky="ew")
            tools.columnconfigure(i % 3, weight=1, uniform="tools")

        self.refresh_status()

    def _menu(self) -> None:
        bar = tk.Menu(self.root)
        lang_menu = tk.Menu(bar, tearoff=False)
        for code, name in i18n.LANGUAGES.items():
            lang_menu.add_radiobutton(label=name, value=code, variable=self.lang_var, command=self.on_language)
        bar.add_cascade(label=t("menu_language", self.lang), menu=lang_menu)
        help_menu = tk.Menu(bar, tearoff=False)
        help_menu.add_command(label=t("menu_guide", self.lang), command=self.on_guide)
        help_menu.add_command(label=t("menu_about", self.lang), command=self.on_about)
        bar.add_cascade(label=t("menu_help", self.lang), menu=help_menu)
        self.root.config(menu=bar)

    def _header(self, parent: tk.Misc) -> None:
        """Night sky, striped sun, neon grid and the name in lights, drawn on a canvas."""
        c = tk.Canvas(parent, width=WIDTH, height=HEADER_H, bg=BG, highlightthickness=0)
        c.pack(fill="x")
        horizon = int(HEADER_H * 0.72)
        steps = 24
        for i in range(steps):  # sky gradient, dark violet to magenta at the horizon
            k = i / (steps - 1)
            colour = "#%02x%02x%02x" % (int(18 + 70 * k), int(0 + 12 * k), int(43 + 60 * k))
            y0 = int(horizon * i / steps)
            c.create_rectangle(0, y0, WIDTH, int(horizon * (i + 1) / steps) + 1, fill=colour, width=0)
        cx, r = WIDTH - 140, 62
        # Sun: one line per pixel row, yellow at the top to pink at the horizon, cut by
        # transparent stripes that get wider towards the bottom.
        gaps, y_gap, gap, band = set(), horizon - int(r * 0.55), 2, int(r * 0.16)
        while y_gap < horizon:
            gaps.update(range(y_gap, y_gap + gap))
            y_gap += gap + band
            gap += 1
            band = max(3, int(band * 0.8))
        for y in range(horizon - r, horizon):
            if y in gaps:
                continue
            half = (r * r - (horizon - y) ** 2) ** 0.5
            k = (y - (horizon - r)) / r
            colour = "#ff%02x%02x" % (int(214 - 173 * k), int(64 + 53 * k))
            c.create_line(cx - half, y, cx + half, y, fill=colour)
        c.create_rectangle(0, horizon, WIDTH, HEADER_H, fill="#0b0019", width=0)
        for i in range(-12, 13):  # perspective grid
            c.create_line(cx + i * 14, horizon, cx + i * 90, HEADER_H, fill=PURPLE)
        y, step = horizon, 3.0
        while y < HEADER_H:
            c.create_line(0, y, WIDTH, y, fill=PURPLE)
            step *= 1.45
            y += step
        title_font = (self.title_family, 34, "bold italic")
        for dx, dy, colour in ((3, 3, "#5a0f3a"), (2, 2, "#8a1650"), (-1, -1, "#ff7aa8")):  # glow
            c.create_text(32 + dx, 52 + dy, text="RIOT OFFICE", anchor="w", font=title_font, fill=colour)
        c.create_text(32, 52, text="RIOT OFFICE", anchor="w", font=title_font, fill=PINK)
        c.create_text(36, 92, text=t("tagline", self.lang), anchor="w", font=(self.body_family, 12, "italic"), fill=CYAN)
        c.create_text(WIDTH - 12, HEADER_H - 10, text=f"v{__version__}", anchor="e",
                      font=(self.body_family, 8), fill=MUTED)

    def _app_card(self, parent: tk.Misc, module: str, colour: str) -> tk.Frame:
        card = tk.Frame(parent, bg=PANEL, highlightthickness=2, highlightbackground=colour, cursor="hand2")
        name = tk.Label(card, text=t(module, self.lang).upper(), bg=PANEL, fg=colour,
                        font=(self.title_family, 18, "bold"), pady=6)
        hint = tk.Label(card, text=t(f"{module}_hint", self.lang), bg=PANEL, fg=MUTED, font=(self.body_family, 9),
                        pady=4)
        name.pack(padx=10, pady=(14, 0))
        hint.pack(padx=10, pady=(0, 14))

        def enter(_):
            for w in (card, name, hint):
                w.configure(bg=colour)
            name.configure(fg=BG)
            hint.configure(fg=BG)

        def leave(_):
            for w in (card, name, hint):
                w.configure(bg=PANEL)
            name.configure(fg=colour)
            hint.configure(fg=MUTED)

        for w in (card, name, hint):
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", lambda _e, m=module: self.on_module(m))
        return card

    def _button(self, parent: tk.Misc, text: str, command, colour: str, small: bool = False) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=BG, fg=colour, activebackground=colour,
                         activeforeground=BG, relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=colour, cursor="hand2", padx=14, pady=6 if small else 8,
                         font=(self.body_family, 10 if small else 11, "bold"))

    def refresh_status(self) -> None:
        if self.inst is None:
            self.status_var.set(t("status_missing", self.lang))
            self.status.configure(fg=YELLOW)
        elif not config.is_installed(self.inst):
            self.status_var.set(t("status_ok", self.lang, version=self.lo_version or "?") + "  ·  "
                                + t("status_no_config", self.lang))
            self.status.configure(fg=YELLOW)
        else:
            self.status_var.set(t("status_ok", self.lang, version=self.lo_version or "?"))
            self.status.configure(fg=MUTED)

    # ----- helpers --------------------------------------------------------------------------
    def _need_lo(self) -> bool:
        if self.inst is None:
            messagebox.showerror("Riot Office", t("status_missing", self.lang), parent=self.root)
            return False
        return True

    def _run(self, job, done_message) -> None:
        """Run ``job`` in a thread; show ``done_message(result)`` or the error when it ends."""
        self.status_var.set(t("working", self.lang))
        self.root.configure(cursor="watch")

        def worker():
            try:
                result = job()
            except Exception as exc:
                traceback.print_exc()
                self.root.after(0, lambda: self._finish(None, str(exc)))
            else:
                self.root.after(0, lambda: self._finish(done_message(result), None))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, message: str | None, error: str | None) -> None:
        self.root.configure(cursor="")
        self.refresh_status()
        if error:
            messagebox.showerror(t("error", self.lang), error, parent=self.root)
        elif message:
            messagebox.showinfo(t("done", self.lang), message, parent=self.root)

    def _files_written(self, paths: list[Path]) -> str:
        return t("done_files", self.lang, count=len(paths), folder=paths[0].parent if paths else "")

    # ----- actions --------------------------------------------------------------------------
    def on_module(self, module: str) -> None:
        if self._need_lo():
            libreoffice.launch(self.inst, module)

    def on_open_file(self) -> None:
        if not self._need_lo():
            return
        files = filedialog.askopenfilenames(parent=self.root)
        if files:
            libreoffice.launch(self.inst, None, [Path(f) for f in files])

    def on_merge(self) -> None:
        files = filedialog.askopenfilenames(parent=self.root, title=t("choose_pdfs", self.lang),
                                            filetypes=[("PDF", "*.pdf *.PDF")])
        if not files:
            return
        out = filedialog.asksaveasfilename(parent=self.root, title=t("save_as", self.lang), defaultextension=".pdf",
                                           initialdir=str(Path(files[0]).parent), filetypes=[("PDF", "*.pdf")])
        if out:
            self._run(lambda: pdftools.merge([Path(f) for f in files], Path(out)), lambda p: self._files_written([p]))

    def on_split(self) -> None:
        src = filedialog.askopenfilename(parent=self.root, title=t("choose_pdf", self.lang),
                                         filetypes=[("PDF", "*.pdf *.PDF")])
        if not src:
            return
        ranges = simpledialog.askstring("Riot Office", t("ask_ranges", self.lang), parent=self.root)
        if ranges is None:
            return
        self._run(lambda: pdftools.split(Path(src), Path(src).parent, ranges), self._files_written)

    def on_rotate(self) -> None:
        src = filedialog.askopenfilename(parent=self.root, title=t("choose_pdf", self.lang),
                                         filetypes=[("PDF", "*.pdf *.PDF")])
        if not src:
            return
        degrees = simpledialog.askinteger("Riot Office", t("ask_degrees", self.lang), parent=self.root,
                                          initialvalue=90, minvalue=90, maxvalue=270)
        if degrees is None:
            return
        pages = simpledialog.askstring("Riot Office", t("ask_pages", self.lang), parent=self.root)
        if pages is None:
            return
        out = filedialog.asksaveasfilename(parent=self.root, title=t("save_as", self.lang), defaultextension=".pdf",
                                           initialfile=f"{Path(src).stem}_rotated.pdf", initialdir=str(Path(src).parent))
        if out:
            self._run(lambda: pdftools.rotate(Path(src), Path(out), degrees, pages), lambda p: self._files_written([p]))

    def on_convert(self) -> None:
        if not self._need_lo():
            return
        files = filedialog.askopenfilenames(parent=self.root, title=t("choose_documents", self.lang))
        if not files:
            return
        pdfa = messagebox.askyesno("Riot Office", t("pdfa_question", self.lang), parent=self.root)
        out_dir = Path(files[0]).parent
        self._run(lambda: libreoffice.convert(self.inst, [Path(f) for f in files], out_dir, "pdf", pdfa=pdfa),
                  self._files_written)

    def on_ocr(self) -> None:
        if not pdftools.ocr_available():
            messagebox.showwarning("Riot Office", t("ocr_missing", self.lang), parent=self.root)
            return
        src = filedialog.askopenfilename(parent=self.root, title=t("choose_pdf", self.lang),
                                         filetypes=[("PDF", "*.pdf *.PDF")])
        if not src:
            return
        out = filedialog.asksaveasfilename(parent=self.root, title=t("save_as", self.lang), defaultextension=".pdf",
                                           initialfile=f"{Path(src).stem}_ocr.pdf", initialdir=str(Path(src).parent))
        if out:
            languages = "ita+eng" if self.lang == "it" else "eng+ita"
            self._run(lambda: pdftools.ocr(Path(src), Path(out), languages), lambda p: self._files_written([p]))

    def on_language(self) -> None:
        code = self.lang_var.get()
        if code == self.lang:
            return
        i18n.set_language(code)
        self.lang = code
        try:
            config.set_ui_locale(i18n.LIBREOFFICE_LOCALES[code])
        except (OSError, ValueError) as exc:
            messagebox.showerror(t("error", code), str(exc), parent=self.root)
        else:
            messagebox.showinfo("Riot Office", t("language_changed", code), parent=self.root)
        self.build()

    def set_language(self, code: str) -> None:
        """Switch the window's language without touching saved settings (used by screenshot tests)."""
        self.lang = code
        self.lang_var.set(code)
        self.build()

    def on_guide(self) -> None:
        if GUIDE.exists():
            webbrowser.open(GUIDE.as_uri())

    def on_about(self) -> None:
        messagebox.showinfo(t("menu_about", self.lang),
                            t("about", self.lang, version=__version__, lo=self.lo_version or "?"), parent=self.root)


def run() -> int:
    """Open the launcher and wait until it is closed."""
    if sys.platform == "win32":
        try:  # crisp text on high-DPI screens
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk(className="riot-office")
    App(root)
    root.mainloop()
    return 0
