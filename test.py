import win32con
import win32gui
import logging
import subprocess

import keyboard

from lib.Shortcuts.ShortcutManager import ManagerOptions, ShortcutManager
from lib.Shortcuts.Shortcut import Shortcut

from typing import Callable, List, Literal


logging.basicConfig()
logging.getLogger("ShortcutManager").setLevel(logging.DEBUG)

logging.getLogger("Shortcut").setLevel(logging.DEBUG)
# logging.getLogger("Shortcut").setLevel(logging.NOTSET)

logging.getLogger("HotkeyWindow").setLevel(logging.DEBUG)


lorem = """
Nostrud ullamco in reprehenderit occaecat minim exercitation proident ea est. 
Mollit minim id qui cupidatat consequat magna nulla anim nisi in. Ipsum voluptate 
aute proident veniam minim ipsum. Consequat elit consectetur fugiat eiusmod 
labore. Ipsum ad esse aliquip cupidatat anim labore ullamco sint dolor non ut.

Commodo cillum consequat incididunt eu aute eiusmod mollit veniam
velit quis aliqua. Irure do esse Lorem quis occaecat pariatur culpa occaecat. Labore 
tempor minim deserunt veniam labore minim non laborum Lorem cillum. Id commodo anim 
labore ea tempor mollit dolore id labore nulla ea. Sint qui laborum duis qui ex laborum
aliqua commodo eu eu do. Cillum ullamco exercitation incididunt laboris aliquip deserunt Lorem.

Sit voluptate elit ad do Lorem et proident irure consectetur.
Et labore non minim et excepteur duis ipsum qui est ipsum. Ex veniam sunt id aliquip
ex. Dolore enim eu Lorem velit nulla eiusmod esse ullamco adipisicing eiusmod cillum
non mollit. Sint nostrud in laboris ut officia et occaecat quis dolore proident fugiat.

Ea enim tempor veniam Lorem ea qui cupidatat esse eu magna ipsum. Esse laboris labore consequat aute.
Reprehenderit mollit ut magna veniam voluptate exercitation Lorem
sit occaecat ea est. Ut tempor et officia ullamco est labore ut eiusmod nostrud quis
proident laborum nulla ad. Ipsum dolore voluptate laborum qui sunt duis enim aute.
"""


class Macros:
    @staticmethod
    def pressKKeyNTimes(K: str, N: int):
        print(f"Pressing {K} {N} times")
        [keyboard.send(K) for _ in range(N)]

    @staticmethod
    def lorem():
        print(f"Lorem Ipsum")

        keyboard.write(lorem)


class Word:
    @staticmethod
    def forward():
        keyboard.send("ctrl+right")

    @staticmethod
    def backward():
        keyboard.send("ctrl+left")


class Select:
    @staticmethod
    def enter():
        keyboard.press("shift")

    @staticmethod
    def exit():
        keyboard.release("shift")

    @staticmethod
    def copy(type: Literal["F10", "CTRL+C"]):
        if type == "F10":
            keyboard.send("shift+F10")
            keyboard.send("c")
            return

        else:
            keyboard.send("ctrl+c")
            return

    @staticmethod
    def selectWord():
        Word.backward()
        Select.enter()
        Word.forward()
        Select.exit()

    @staticmethod
    def yankWord():
        Select.selectWord()
        Select.copy()


class Navigation:
    @staticmethod
    def to(type: Literal["top", "bottom"]):
        if type == "top":
            keyboard.send("ctrl+home")
            return
        else:
            keyboard.send("ctrl+end")
            return


def main():
    manager: ShortcutManager = ShortcutManager(
        "ctrl+up", options=ManagerOptions(requireFullPath=True)
    )
    manager.addShortcut(
        Shortcut(
            "note",
            lambda: subprocess.run("notepad.exe"),
        )
    )
    manager.addShortcut(
        Shortcut(
            list("bvw"),
            Select.selectWord,
        )
    ),
    manager.addShortcut(
        Shortcut(
            list("vw"),
            Select.selectWord,
        )
    ),
    manager.addShortcut(
        Shortcut(
            list("gg"),
            lambda: Navigation.to("top"),
        )
    ),
    manager.addShortcut(
        Shortcut(
            ["shift+g", "shift+g"],
            lambda: Navigation.to("bottom"),
        )
    ),
    manager.addShortcut(
        Shortcut(
            list("lorem"),
            Macros.lorem,
        )
    )

    ShortcutManager.wait()


main()
