from importlib.metadata import PackageNotFoundError, metadata

try:
    NAME = metadata("simple_api")["Name"]
    VERSION = metadata("simple_api")["Version"]
except (PackageNotFoundError, KeyError):
    NAME = "unknown"
    VERSION = "unknown"
