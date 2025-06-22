import tkinter as tk
from app.app import ModernCodeExtractorGUI

if __name__ == "__main__":
    """
    Main entry point for the Code Extractor Pro application.
    """
    root = tk.Tk()
    app = ModernCodeExtractorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
