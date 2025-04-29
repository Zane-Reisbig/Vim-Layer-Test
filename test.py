import logging
import subprocess

from lib.ShortcutManager import ManagerOptions, ShortcutManager
from lib.Shortcut import Shortcut

logging.basicConfig()

logging.getLogger("ShortcutManager").setLevel(logging.DEBUG)

# logging.getLogger("Shortcut").setLevel(logging.DEBUG)
logging.getLogger("Shortcut").setLevel(logging.NOTSET)


def openPaint():
    subprocess.run("mspaint.exe")


def main():
    manager = ShortcutManager("ctrl+g")

    manager.addShortcut(Shortcut(list("paint"), openPaint, "Open Paint"))

    ShortcutManager.wait()


main()
