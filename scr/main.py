import os
import htmlPy
from PyQt4 import QtGui

# Define function to import external files when using PyInstaller.
def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Initial confiurations
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# GUI initializations
app = htmlPy.AppGUI(title="MTAAC annotation assistant",
                    maximized=False,
                    plugins=True)

# GUI configurations
app.static_path = os.path.join(BASE_DIR, "static/")
app.template_path = os.path.join(BASE_DIR, "templates/")

app.web_app.setMinimumWidth(600)
app.web_app.setMinimumHeight(500)
#app.window.setWindowIcon(QtGui.QIcon(BASE_DIR + "/static/img/icon.png"))

# Binding of back-end functionalities with GUI

# Import back-end functionalities
from functions import Dashboard

##from html_to_python import ClassName

# Register back-end functionalities
app.bind(Dashboard(app))

# Instructions for running application
if __name__ == "__main__":
    # The driver file will have to be imported everywhere in back-end.
    # So, always keep app.start() in if __name__ == "__main__" conditional
    app.start()

    
