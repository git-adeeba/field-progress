from typing import Optional

from pydantic import BaseModel


class ParsedInputItem(BaseModel):
    raw_text: str

    discipline: Optional[str] = None
    area: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None

    source_row: Optional[int] = None