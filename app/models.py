from pydantic import BaseModel, Field, validator
import datetime 
from typing import Optional

class StockMetadata(BaseModel):
    id: Optional[int] = None
    symbol: str
    name: str

class DailyData(BaseModel):
    id: Optional[int] = None
    stock_id: int
    date: datetime.date
    market_cap: float
    price: float

class IndexComposition(BaseModel):
    id: Optional[int] = None
    date: datetime.date
    stock_id: int
    weight: float

class IndexPerformance(BaseModel):
    id: Optional[int] = None
    date: datetime.date
    index_value: float
    daily_return: Optional[float] = None
    cumulative_return: Optional[float] = None

class BuildIndexRequest(BaseModel):
    start_date: datetime.date
    end_date: Optional[datetime.date] = None

    @validator('end_date')
    def validate_end_date(cls, end_date, values):
        start_date = values.get('start_date')
        if end_date and start_date and end_date < start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return end_date
    @validator('start_date', pre=True)
    def parse_start_date(cls, value):
        if isinstance(value, str):
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        return value
    @validator('end_date', pre=True)
    def parse_end_date(cls, value):
        if isinstance(value, str):
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        return value
class ExportDataRequest(BaseModel):
    start_date: str
    end_date: Optional[str] = None
