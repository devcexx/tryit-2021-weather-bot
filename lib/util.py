import os


def get_environ(var: str) -> str:
    value = os.environ.get(var)
    if value is None:
        raise Exception(f"Required env var not set: {var}")
    return value
