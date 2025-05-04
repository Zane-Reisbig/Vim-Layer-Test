import logging

from typing import Callable

logger = logging.getLogger("Shortcut")


class Shortcut:
    label: str
    path: list[str]
    runnable: Callable[[], None]
    onBeforeRun: Callable[[int], None]
    lastCheckedStep: int

    def __init__(
        self,
        path: list[str],
        runnable: Callable[[], None],
        onBeforeRun: Callable[[int], None] = None,
        label: str = None,
    ):
        self.path = path
        self.runnable = runnable
        self.onBeforeRun = onBeforeRun

        self.lastCheckedStep = 1

        self.label = label
        if not self.label:
            self.label = f"{" ->".join(path[0:min(len(path), 3)])}"

    def run(self):
        logger.debug(
            f"Running Macro: '{self.label}' after '{self.lastCheckedStep}' steps"
        )
        if self.onBeforeRun:
            self.onBeforeRun(self.lastCheckedStep)

        self.runnable()

    def reset(self):
        self.lastCheckedStep = 1

    def matchesStep(self, steps: list[str]):
        if len(steps) == 0:
            return False

        otherSteps = "".join(steps)
        selfSteps = "".join(self.path[0 : len(steps)])

        logger.debug(f"Other step: {otherSteps}")
        logger.debug(f"This step: {selfSteps}")

        return otherSteps == selfSteps

    def getKeyForStep(self, steps: list[str]):
        self.lastCheckedStep = len(steps) + 1

        if len(steps) > len(self.path):
            return None

        if len(steps) == len(self.path):
            return self.path[len(steps) - 1]

        return self.path[len(steps)]

    def __repr__(self):
        return f"Shortcut(path='{" ->".join(self.path)}', label='{self.label}')"
