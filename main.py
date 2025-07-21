import ttkbootstrap as ttkb
from app.app import ModernCodeExtractorGUI
import sys

if __name__ == "__main__":
    """
    Main entry point for the PandaBrew application.
    """
    # Use ttkbootstrap Window with the 'darkly' theme
    root = ttkb.Window(themename="darkly")

    # Conditionally apply Windows-specific styling for a native look and feel
    if sys.platform == "win32":
        try:
            import pywinstyles
            # Apply a dark, mica style to the window for better performance
            pywinstyles.apply_style(root, "mica")
            # Set a lighter, less saturated blue tint color
            pywinstyles.set_opacity(root, color="#2c3e50")
            print("Applied Windows-specific styling.")
        except ImportError:
            print("pywinstyles not found, skipping Windows-specific styling.")


    app = ModernCodeExtractorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
