from typing import Any


class Config:
    def __init__(self, data: dict):
        self._data = data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def to_dict(self) -> dict:
        return self._data.copy()

    def __repr__(self) -> str:
        return f"Config({self.to_dict()})"
