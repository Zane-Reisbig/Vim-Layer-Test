from __future__ import annotations

from threading import Event, Thread
from tkinter import Label, Tk, Entry, Text, StringVar
import enum
import logging
import os

from typing import Callable, List, Tuple


class Constants:
    MACRO_INPUT = "MACRO_INPUT"
    HELP_TEXT = "HELP_TEXT"


class T_WindowMessage(enum.Enum):
    SET_HELP_TEXT = 0
    SET_MACRO_INPUT = 1
    LIFT_WINDOW = 2


class WindowMessage:
    type: T_WindowMessage
    args: Tuple

    def __init__(self, type: T_WindowMessage, *args):
        self.type = type
        self.args = args

    def __repr__(self):
        return f"WindowMessage(type={self.type}, args={self.args})"


class WindowThreadWrapper:
    preQueue: List[WindowMessage]
    waiterThread: Thread

    windowThread: Thread
    windowRef: HotkeyWindow | None = None

    postMessage: Callable[[T_WindowMessage], None] = None

    def __init__(self):
        self.preQueue = list()

        logger.debug("Setting post message")
        logger.debug("Waiting for window reference, ORIGINAL")

        haveRefEvent = self.__generateEvent()

        def threadWrapper():
            logger.debug("Started new hotkey window")
            self.windowRef = HotkeyWindow()
            haveRefEvent.set()

            self.windowRef.root.geometry("50x100")

            # Kills process on window close
            self.windowRef.root.wm_protocol("WM_DELETE_WINDOW", lambda: os._exit(0))

            # Start window minimized
            self.windowRef.root.iconify()

            self.windowRef.start()

        self.windowThread = Thread(
            target=threadWrapper,
            name="Hotkey-Input-Window",
        )

        self.windowThread.start()
        haveRefEvent.wait()

    def __generateEvent(self):
        return Event()


class HotkeyWindow:
    root: Tk

    macroEntry: Entry
    entryValue: StringVar

    helpText: Text

    @property
    def helpTextValue(self):
        return self.helpText.get(1.0, "end")

    def __init__(self):
        logger.debug("We are inside the Hotkey window")
        self.root = Tk()
        self.root.title("Macro Input")

        entryLabel = Label(self.root, text="Listening...")
        entryLabel.pack()

        self.entryValue = StringVar(self.root, "", Constants.MACRO_INPUT)
        self.macroEntry = Entry(
            self.root,
            textvariable=self.entryValue,
            font="monospace",
            relief="sunken",
            state="readonly",
        )
        self.macroEntry.pack()

        self.helpText = Text(
            self.root,
            font="monospace",
            relief="sunken",
            state="disabled",
        )
        self.helpText.pack()

    def start(self):
        self.root.mainloop()

    def updateEntry(self, value: str):
        self.entryValue.set(value)
        self.macroEntry.setvar(Constants.MACRO_INPUT, value)

    def updateHelpText(self, value: str):
        self.helpText.insert(1.0, value, "end")


logger = logging.getLogger("HotkeyWindow")
