"""Tkinter desktop GUI launcher."""
from gui.app import BarcodeProcessorApp


def main():
    app = BarcodeProcessorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
