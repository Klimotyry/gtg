import os


def service_id() -> str:
    return os.getenv("BYTECOIN_SERVICE_ID", "").strip()


def transfer_url() -> str:
    value = os.getenv("BYTECOIN_TRANSFER_URL", "").strip()
    if value:
        return value
    sid = service_id()
    return f"https://t.me/byteappbot/app?startapp=transfer-{sid}" if sid else ""


def admin_username() -> str:
    return os.getenv("ADMIN_USERNAME", "MrSerPull").strip().lstrip("@")
