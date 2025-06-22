import ttkbootstrap as ttkb
from app.app import ModernCodeExtractorGUI
import pywinstyles

if __name__ == "__main__":
    """
    Main entry point for the PandaBrew application.
    """
    # Use ttkbootstrap Window with the 'darkly' theme
    root = ttkb.Window(themename="darkly")

    # Apply a dark, mica style to the window for better performance
    pywinstyles.apply_style(root, "mica")
    # Set a lighter, less saturated blue tint color
    pywinstyles.set_opacity(root, color="#2c3e50")

    app = ModernCodeExtractorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
