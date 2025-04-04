from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlmodel import JSON, Field, SQLModel


class Competitor(BaseModel):
    name: str
    market_cap: dict = Field(sa_type=MutableDict.as_mutable(JSON), nullable=True)


class Stock(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(default=None, nullable=True)
    purchased_amount: Decimal = Field(default=0, max_digits=9, decimal_places=2)
    purchased_status: str = Field(default=None, nullable=True)
    # request_data looks more like the content of the request, request_date is the datetime we made the request.
    request_date: datetime = Field(default=None, nullable=True)
    company_code: str = Field(index=True)
    company_name: str = Field(default=None, nullable=True)
    # Todo: split in more pydantic models
    stock_values: dict = Field(sa_type=MutableDict.as_mutable(JSON), nullable=True)
    performance_data: dict = Field(sa_type=MutableDict.as_mutable(JSON), nullable=True)
    competitors: List[Competitor] = Field(
        sa_type=MutableList.as_mutable(JSON), nullable=True, default=[]
    )
