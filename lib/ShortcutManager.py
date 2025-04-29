from __future__ import annotations

import keyboard
import threading
import logging

from lib.Shortcut import Shortcut
from typing import Any, Callable, Dict, Literal

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

logger = logging.getLogger("ShortcutManager")


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

    def __init__(self, addDummyShortcut: bool = True):
        self.addDummyShortcut = addDummyShortcut

    def setIfNot[T](self, key: Literal["addDummyShortcut"], to: T):
        if getattr(self, key) is not None:
            return

        setattr(self, key, to)


class ShortcutManager:
    cmdKey: str
    breakoutHotkey: str
    options: ManagerOptions
    pathAccumulator: list[str]

    shortcuts: list[Shortcut]

    def __init__(
        self, cmdHotkey: str, breakoutHotkey: str = None, options: ManagerOptions = None
    ):
        self.cmdKey = cmdHotkey
        self.breakoutHotkey = breakoutHotkey or "esc"
        self.shortcuts = list()
        self.pathAccumulator = list()
        self.options = options or ManagerOptions()

        self.__unhookAllKeys()
        self.__hookCmdKey()

        if self.options.addDummyShortcut:
            self.addShortcut(
                shortcut=Shortcut(
                    "f16", lambda: logger.debug("How'd we get here?"), "Dummy!"
                )
            )

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
        def onPressPreHook():
            logger.debug(f"Key: {KeyCode(key)} pressed")
            onPress(KeyCode(key), *Option.get(args))

        keyboard.add_hotkey(key, onPressPreHook)

    def __hookCmdKey(self):
        self.__hookKey(self.cmdKey, self.__onCommandKeyPressed)

    def __runFoundShortcut(self, shortcut: Shortcut):
        logger.debug("Running shortcut!")
        threading.Thread(target=lambda: self.runShortcut(shortcut)).start()
        self.__cleanup()

    def __cleanup(self):
        self.pathAccumulator = list()
        self.__unhookAllKeys()
        self.__hookCmdKey()

    def __hookCurrentPaths(self):
        self.__unhookAllKeys()

        validPaths: list[Shortcut] = []

        for path in self.shortcuts:
            if not path.matchesStep(self.pathAccumulator):
                continue

            validPaths.append(path)

        logger.debug(f"All valid paths -")
        for path in validPaths:
            logger.debug(f"{repr(path)}")

        if len(validPaths) == 1:
            #
            # This is where we've found the shortcut
            #
            self.__runFoundShortcut(validPaths[0])
            return

        def onHookPressLogic(keyCode: KeyCode, *args: list[Any]):
            logger.debug(f"Key pressed: {keyCode.code}")
            self.pathAccumulator.append(keyCode.code)
            self.__hookCurrentPaths()

        def onBreakoutHotkeyPressed(keyCode: KeyCode, *args: list[Any]):
            logger.debug("Breakout!")
            self.__cleanup()

        # Wait we fucked up- key
        self.__hookKey(self.breakoutHotkey, onBreakoutHotkeyPressed)

        hooked = []
        for path in self.shortcuts:
            stepKey = path.getKeyForStep(self.pathAccumulator)

            if stepKey in hooked:
                continue

            hooked.append(stepKey)
            hasNextKey = path.getKeyForStep(self.pathAccumulator)

            if not hasNextKey:
                continue

            self.__hookKey(hasNextKey, onHookPressLogic)

    def __onCommandKeyPressed(self, key: str):
        logger.debug("Command Key pressed")
        self.__unhookAllKeys()
        self.__hookCurrentPaths()

    def addShortcut(self, shortcut: Shortcut):
        self.shortcuts.append(shortcut)

    def runShortcut(self, shortcut: Shortcut):
        shortcut.run()

    @staticmethod
    def wait(forCmdHotkey: str = None):
        keyboard.wait(forCmdHotkey)
