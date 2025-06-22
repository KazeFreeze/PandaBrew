import ttkbootstrap as ttkb
from app.app import ModernCodeExtractorGUI
import pywinstyles

if __name__ == "__main__":
    """
    Main entry point for the Code Extractor Pro application.
    """
    # Use ttkbootstrap Window
    root = ttkb.Window(themename="litera")
    pywinstyles.apply_style(root, "dark")
    app = ModernCodeExtractorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
