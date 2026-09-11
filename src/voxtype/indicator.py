# ruff: noqa: F821

import asyncio
import logging
import os
import threading
from collections.abc import Callable

from dbus_next.aio import MessageBus
from dbus_next.constants import PropertyAccess
from dbus_next.service import ServiceInterface, dbus_property, method, signal

LOG = logging.getLogger("voxtype.indicator")
SIZE = 22


def _canvas() -> list[list[tuple[int, int, int, int]]]:
    return [[(0, 0, 0, 0) for _ in range(SIZE)] for _ in range(SIZE)]


def _circle(canvas, cx: int, cy: int, radius: int, color) -> None:
    for y in range(SIZE):
        for x in range(SIZE):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius**2:
                canvas[y][x] = color


def _rect(canvas, x1: int, y1: int, x2: int, y2: int, color) -> None:
    for y in range(max(0, y1), min(SIZE, y2)):
        for x in range(max(0, x1), min(SIZE, x2)):
            canvas[y][x] = color


def _icon(state: str) -> list[list[object]]:
    """Return one SNI ARGB32 pixmap as a(width, height, bytes)."""
    canvas = _canvas()
    if state == "recording":
        _circle(canvas, 11, 11, 9, (244, 67, 54, 255))
        _rect(canvas, 9, 5, 13, 13, (255, 255, 255, 255))
        _rect(canvas, 7, 10, 9, 14, (255, 255, 255, 255))
        _rect(canvas, 13, 10, 15, 14, (255, 255, 255, 255))
        _rect(canvas, 9, 14, 13, 16, (255, 255, 255, 255))
        _rect(canvas, 10, 16, 12, 19, (255, 255, 255, 255))
    elif state in {"transcribing", "loading"}:
        color = (255, 179, 0, 255)
        _circle(canvas, 11, 11, 9, color)
        for x, top in ((6, 9), (9, 6), (12, 4), (15, 8)):
            _rect(canvas, x, top, x + 2, 18 - top // 2, (255, 255, 255, 255))
    elif state == "error":
        _circle(canvas, 11, 11, 9, (244, 67, 54, 255))
        _rect(canvas, 10, 5, 12, 13, (255, 255, 255, 255))
        _rect(canvas, 10, 15, 12, 18, (255, 255, 255, 255))
    else:
        # Quiet blue microphone while ready.
        color = (98, 160, 234, 255)
        _rect(canvas, 8, 3, 14, 13, color)
        _circle(canvas, 11, 5, 3, color)
        _rect(canvas, 6, 10, 8, 15, color)
        _rect(canvas, 14, 10, 16, 15, color)
        _rect(canvas, 8, 14, 14, 17, color)
        _rect(canvas, 10, 17, 12, 20, color)

    # The SNI protocol carries 32-bit ARGB pixels in network byte order.
    pixels = bytearray()
    for row in canvas:
        for red, green, blue, alpha in row:
            pixels.extend((alpha, red, green, blue))
    return [[SIZE, SIZE, bytes(pixels)]]


class StatusItem(ServiceInterface):
    def __init__(self, activate: Callable[[], None]) -> None:
        super().__init__("org.kde.StatusNotifierItem")
        self.state = "loading"
        self.activate_callback = activate

    @dbus_property(access=PropertyAccess.READ)
    def Category(self) -> "s":
        return "Hardware"

    @dbus_property(access=PropertyAccess.READ)
    def Id(self) -> "s":
        return "voxtype"

    @dbus_property(access=PropertyAccess.READ)
    def Title(self) -> "s":
        return {
            "idle": "VoxType — ready",
            "recording": "VoxType — listening",
            "transcribing": "VoxType — transcribing",
            "loading": "VoxType — loading model",
            "error": "VoxType — error",
        }.get(self.state, "VoxType")

    @dbus_property(access=PropertyAccess.READ)
    def Status(self) -> "s":
        return "NeedsAttention" if self.state in {"recording", "error"} else "Active"

    @dbus_property(access=PropertyAccess.READ)
    def WindowId(self) -> "u":
        return 0

    @dbus_property(access=PropertyAccess.READ)
    def IconName(self) -> "s":
        return ""

    @dbus_property(access=PropertyAccess.READ)
    def IconThemePath(self) -> "s":
        return ""

    @dbus_property(access=PropertyAccess.READ)
    def IconPixmap(self) -> "a(iiay)":
        return _icon(self.state)

    @dbus_property(access=PropertyAccess.READ)
    def ItemIsMenu(self) -> "b":
        return False

    @dbus_property(access=PropertyAccess.READ)
    def Menu(self) -> "o":
        # COSMIC probes this property even when the item has no context menu.
        return "/NO_DBUSMENU"

    @method()
    def Activate(self, x: "i", y: "i"):
        del x, y
        threading.Thread(target=self.activate_callback, daemon=True).start()

    @method()
    def SecondaryActivate(self, x: "i", y: "i"):
        del x, y
        threading.Thread(target=self.activate_callback, daemon=True).start()

    @method()
    def ContextMenu(self, x: "i", y: "i"):
        del x, y

    @method()
    def Scroll(self, delta: "i", orientation: "s"):
        del delta, orientation

    @method()
    def ProvideXdgActivationToken(self, token: "s"):
        del token

    @signal()
    def NewIcon(self):
        return None

    @signal()
    def NewTitle(self):
        return None

    @signal()
    def NewStatus(self, status) -> "s":
        return status

    def update(self, state: str) -> None:
        self.state = state
        self.emit_properties_changed(
            {"Title": self.Title, "Status": self.Status, "IconPixmap": self.IconPixmap}
        )
        self.NewTitle()
        self.NewIcon()
        self.NewStatus(self.Status)


class StatusIndicator:
    def __init__(self, activate: Callable[[], None]) -> None:
        self.activate = activate
        self.loop: asyncio.AbstractEventLoop | None = None
        self.item: StatusItem | None = None
        self.pending_state = "loading"

    def start(self) -> None:
        threading.Thread(
            target=self._run, name="voxtype-indicator", daemon=True
        ).start()

    def set_state(self, state: str) -> None:
        self.pending_state = state
        if self.loop is not None and self.item is not None:
            self.loop.call_soon_threadsafe(self.item.update, state)

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        self.loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._register())
            loop.run_forever()
        except Exception:
            LOG.exception("Could not register the COSMIC status indicator")

    async def _register(self) -> None:
        bus = await MessageBus().connect()
        item = StatusItem(self.activate)
        self.item = item
        bus.export("/StatusNotifierItem", item)
        service_name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
        await bus.request_name(service_name)
        introspection = await bus.introspect(
            "org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher"
        )
        watcher = bus.get_proxy_object(
            "org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher", introspection
        ).get_interface("org.kde.StatusNotifierWatcher")
        await watcher.call_register_status_notifier_item(service_name)
        item.update(self.pending_state)
        LOG.info("COSMIC status indicator registered")


# ruff: noqa: F821
