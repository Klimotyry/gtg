import os

DEFAULT_SERVICE_ID = "d1682741753621c779c12c92"
DEFAULT_TRANSFER_URL = "https://t.me/byteappbot/app?startapp=transfer-d1682741753621c779c12c92"
DEFAULT_ADMIN_USERNAME = "MrSerPull"


def service_id() -> str:
    return os.getenv("BYTECOIN_SERVICE_ID", DEFAULT_SERVICE_ID).strip()


def transfer_url() -> str:
    value = os.getenv("BYTECOIN_TRANSFER_URL", DEFAULT_TRANSFER_URL).strip()
    if value:
        return value
    sid = service_id()
    return f"https://t.me/byteappbot/app?startapp=transfer-{sid}"


def admin_username() -> str:
    return os.getenv("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME).strip().lstrip("@")
