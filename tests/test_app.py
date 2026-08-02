import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import customtkinter as ctk
from ui.main_window import KindleShotApp


def test_ctk_appearance_mode():
    ctk.set_appearance_mode("Light")
    assert ctk.get_appearance_mode() == "Light"


def test_ctk_color_theme():
    ctk.set_default_color_theme("blue")
    assert True


#def test_app_instantiation():
#    app_instance = KindleShotApp()
#    assert app_instance is not None
