from pathlib import Path
from typing import Self

from pydantic import BaseModel


class Cookie(BaseModel):
    name: str
    value: str
    domain: str
    path: str
    expires: float | None = None
    httpOnly: bool
    secure: bool
    sameSite: str


class LocalStorageItem(BaseModel):
    name: str
    value: str


class Origin(BaseModel):
    origin: str
    localStorage: list[LocalStorageItem]


class DataModel(BaseModel):
    cookies: list[Cookie]
    origins: list[Origin]

    @classmethod
    def from_file(cls, file_path: str | Path) -> Self:
        file_path = Path(file_path)
        return cls.model_validate_json(file_path.read_text(encoding="utf-8"))

    def write_file(self, file_path: Path | str) -> None:
        file_path = Path(file_path)
        file_path.write_text(
            self.model_dump_json(indent=4, exclude_none=True), encoding="utf-8"
        )


if __name__ == "__main__":
    from rich import print as rprint

    data = DataModel.from_file("target_login.json")

    data.write_file("target_login_copy.json")

    rprint(data)
