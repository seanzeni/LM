from pathlib import Path

from app.core.app_context import AppContext
from app.ui.main_window import MainWindow


def main():

    base_dir = Path(__file__).resolve().parent

    context = AppContext(
        base_dir=base_dir,
        settings_path=base_dir / "settings.json",
    )

    window = MainWindow(context)

    window.mainloop()


if __name__ == "__main__":
    main()
