"""CI check: open the launcher on a virtual display and take a screenshot in every language.

    xvfb-run -a python3 ci/gui_screenshots.py <output folder>

Needs ImageMagick's ``import`` on Linux. Fails if the window cannot be built in any language.
"""

import subprocess
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from riot_office import gui, i18n  # noqa: E402


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    root = tk.Tk(className="riot-office")
    app = gui.App(root)
    root.geometry("+0+0")
    codes = list(i18n.LANGUAGES)

    def shot(i: int) -> None:
        if i == len(codes):
            root.destroy()
            return
        app.set_language(codes[i])
        root.update()

        def grab():
            dest = out / f"launcher_{codes[i]}.png"
            # On X11 the menu bar sits above the area Tk measures: add its height (winfo_rooty) to the crop.
            height = root.winfo_height() + root.winfo_rooty()
            subprocess.run(["import", "-window", "root", "-crop", f"{root.winfo_width()}x{height}+0+0", str(dest)],
                           check=True)
            print("screenshot", dest)
            shot(i + 1)

        root.after(800, grab)

    root.after(1500, lambda: shot(0))
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
