from ui.main_window import ModernUI
import os

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("scripts", exist_ok=True)
    os.makedirs("ui", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("output/rois", exist_ok=True)
    
    app = ModernUI()
    app.mainloop()
