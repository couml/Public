from __future__ import annotations

PRINTER_BRANDS: list[str] = [
    "HP", "Canon", "Epson", "Brother", "Kyocera",
    "Ricoh", "Xerox", "Samsung", "Lexmark", "Dell",
]

PAPER_SIZES: list[str] = [
    "A4", "A3", "Letter", "Legal", "B5", "A5",
]

PRINT_STATUSES: list[str] = [
    "queued", "converting", "waiting", "printing",
    "completed", "failed", "cancelled",
]

DEVICE_STATUSES: list[str] = [
    "online", "offline", "busy", "error",
]

ALERT_TYPES: list[str] = [
    "paper_out", "paper_jam", "paper_low",
    "toner_low", "toner_empty", "offline",
    "service_required", "fuser_warning", "drum_low",
]

USER_ROLES: list[str] = [
    "admin", "it_staff", "user",
]

TARGET_FORMATS: list[str] = [
    "original", "pdf", "pcl", "postscript",
]

CHUNK_SIZE: int = 5 * 1024 * 1024  # 5MB
