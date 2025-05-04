from __future__ import annotations

from time import sleep

import keyboard
import threading
import logging

from lib.Shortcuts.Shortcut import Shortcut
from typing import Any, Callable, Dict, Literal

from lib.Window.HotkeyWindow import T_WindowMessage, WindowMessage, WindowThreadWrapper
from lib.WindowManager import Window, getForegroundWindowAsObject


# shortcut
#   - path
#       - list of keys to traverse
#   - action


# manager
#   - hooks command key
#       - makes a list of all traversal paths
#       - hooks all keys and waits for first input <IN>
#       - onkeypress check <IN> against current traversal character
#       - remove all paths not in <IN>
#       - repeat until one path remains
#
#       - last path must be ours!
#       - run shortcut
#       - reset all keys
#       - end function


class KeyCode:
    code: str
    parsedHotkey: tuple[tuple[tuple[int, ...], ...], ...]

    def __init__(self, code: str):
        self.code = code
        self.parsedHotkey = keyboard.parse_hotkey(code)

    def __repr__(self):
        return f"KeyCode(code={self.code}, parsed={self.parsedHotkey})"


class Option[T]:
    @staticmethod
    def has(cls: Option):
        return cls.value is not None

    @staticmethod
    def get(cls: Option):
        return cls.value

    value: T | None

    def __init__(self, value: T | None):
        self.value = value


class ManagerOptions:
    addDummyShortcut: bool
    requireFullPath: bool

    def __init__(self, addDummyShortcut: bool = True, requireFullPath: bool = False):
        self.addDummyShortcut = addDummyShortcut
        self.requireFullPath = requireFullPath


class ShortcutManager:
    this: ShortcutManager

    cmdKey: str
    breakoutHotkey: str
    onBreakout: Callable[[], None]
    onExit: Callable[[], None]
    options: ManagerOptions
    pathAccumulator: list[str]
    targetWindow: Window

    shortcuts: list[Shortcut]

    windowManager: WindowThreadWrapper

    def __init__(
        self,
        cmdHotkey: str,
        breakoutHotkey: str = None,
        onBreakout: Callable[[], None] = lambda: (),
        onCommandRun: Callable[[], None] = lambda: (),
        options: ManagerOptions = None,
    ):
        self.windowManager = WindowThreadWrapper()
        self.cmdKey = cmdHotkey
        self.breakoutHotkey = breakoutHotkey or "esc"
        self.onBreakout = onBreakout
        self.onExit = onCommandRun

        self.shortcuts = list()
        self.pathAccumulator = list()
        self.options = options or ManagerOptions()

        self.__unhookAllKeys()
        self.__hookCmdKey()

        if self.options.addDummyShortcut:
            self.addShortcut(
                shortcut=Shortcut(
                    [
                        "f16",
                    ],
                    lambda: logger.debug("How'd we get here?"),
                    "Dummy!",
                )
            )

    def __dispatch(self, target: Callable[[], None], name: str = "Dispatched Thread"):
        thread = threading.Thread(target=target, name=name)
        thread.start()
        return thread

    def __unhookAllKeys(self):
        try:
            keyboard.remove_all_hotkeys()
        except:
            logger.debug("No hotkeys to remove...")

    def __hookKey[T = None](
        self,
        key: str,
        onPress: Callable[[KeyCode, T], None],
        args: Option[T] = Option(value=()),
    ):
        logger.debug(f"Hotkey: {repr(key)} added")

        def onPressPreHook():
            logger.debug(f"Key: {KeyCode(key)} pressed")
            onPress(KeyCode(key), *Option.get(args))

        keyboard.add_hotkey(key, onPressPreHook)

    def __hookCmdKey(self):
        self.__hookKey(self.cmdKey, self.__onCommandKeyPressed)

    def __cleanup(self):
        self.pathAccumulator = list()
        self.__unhookAllKeys()
        self.__hookCmdKey()

        [shortcut.reset() for shortcut in self.shortcuts]

        # Clear GUI Text
        def clearText():
            self.windowManager.windowRef.updateEntry("")
            self.windowManager.windowRef.updateHelpText("")

        self.__dispatch(target=clearText, name="Clear-Text")

        # Minimize GUI
        self.__dispatch(
            target=self.windowManager.windowRef.root.iconify, name="Iconify"
        )

        if self.onExit:
            self.onExit()

        return

    def __hookCurrentPaths(self):
        self.__unhookAllKeys()

        validPaths: list[Shortcut] = []

        for path in self.shortcuts:
            if len(self.pathAccumulator) != 0 and not path.matchesStep(
                self.pathAccumulator
            ):
                continue

            validPaths.append(path)

        if len(validPaths) == 1:
            #
            # This is where we've found the shortcut
            #

            firstShortcut = validPaths[0]
            fullPathCheck = len(self.pathAccumulator) >= len(firstShortcut.path)

            if self.options.requireFullPath and not fullPathCheck:
                # Just let it keep going if strict
                logger.debug(f"Strict Mode Enabled!")
                logger.debug(
                    f"{len(self.pathAccumulator)} out of {len(firstShortcut.path) - len(self.pathAccumulator)} keys remaining"
                )
                pass
            else:
                # Otherwise we run that shit yo
                self.__runFoundShortcut(firstShortcut)
                self.__cleanup()
                return

        def onHookPressLogic(keyCode: KeyCode, *args: list[Any]):
            logger.debug(f"Key pressed: {keyCode.code}")
            self.pathAccumulator.append(keyCode.code)
            self.__hookCurrentPaths()

            # GUI Stuff
            def updateGUI():
                self.windowManager.windowRef.updateEntry("+".join(self.pathAccumulator))
                self.windowManager.windowRef.updateHelpText(
                    "Valid Paths:\n"
                    + "\n".join(["+".join(shortcut.path) for shortcut in validPaths])
                )

            self.__dispatch(updateGUI, "GUI-Update")

        # Wait we fucked up key
        def onBreakoutHotkeyPressed(keyCode: KeyCode, *args: list[Any]):
            logger.debug("Breakout!")
            self.onBreakout()
            self.__cleanup()

        logger.debug(f"All valid paths -")

        for path in validPaths:
            logger.debug(f"{repr(path)}")

            self.__hookKey(path.getKeyForStep(self.pathAccumulator), onHookPressLogic)

        self.__hookKey(self.breakoutHotkey, onBreakoutHotkeyPressed)

    def __runFoundShortcut(self, shortcut: Shortcut):
        logger.debug("Running shortcut!")

        # Re-activate targeted window
        self.targetWindow.tryActivate()

        # Cheeky little "what if the window isn't raised yet" check
        sleep(0.2)

        threading.Thread(target=lambda: self.runShortcut(shortcut)).start()

    def __onCommandKeyPressed(self, key: KeyCode):
        logger.debug("Command Key pressed")

        # Get a reference to users current window
        self.targetWindow: Window = getForegroundWindowAsObject()

        # Show GUI
        self.windowManager.windowRef.root.deiconify()

        self.__unhookAllKeys()
        self.__hookCurrentPaths()

    def addShortcut(self, shortcut: Shortcut):
        self.shortcuts.append(shortcut)

    def runShortcut(self, shortcut: Shortcut):
        shortcut.run()

    @staticmethod
    def wait(forCmdHotkey: str = None):
        keyboard.wait(forCmdHotkey)

    @staticmethod
    def get(leaderHotkey: str = None) -> ShortcutManager:
        if ShortcutManager.this is None:
            setattr(ShortcutManager, "this", ShortcutManager(leaderHotkey))

        else:
            return getattr(ShortcutManager, "this")


logger = logging.getLogger("ShortcutManager")
