from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class EmployeeBase(BaseModel):
    employee_code: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=1, max_length=150)
    age: Optional[int] = Field(default=None, ge=18, le=100)
    department: Optional[str] = None
    job_role: Optional[str] = None
    monthly_income: Optional[float] = Field(default=None, ge=0)
    years_at_company: Optional[float] = Field(default=None, ge=0, le=80)
    overtime: Optional[str] = None
    job_satisfaction: Optional[int] = Field(default=None, ge=1, le=4)
    work_life_balance: Optional[int] = Field(default=None, ge=1, le=4)

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    employee_code: Optional[str] = Field(default=None, min_length=1, max_length=30)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    age: Optional[int] = Field(default=None, ge=18, le=100)
    department: Optional[str] = None
    job_role: Optional[str] = None
    monthly_income: Optional[float] = Field(default=None, ge=0)
    years_at_company: Optional[float] = Field(default=None, ge=0, le=80)
    overtime: Optional[str] = None
    job_satisfaction: Optional[int] = Field(default=None, ge=1, le=4)
    work_life_balance: Optional[int] = Field(default=None, ge=1, le=4)

class EmployeeOut(EmployeeBase):
    id: int
    created_at: Optional[object] = None
    model_config = ConfigDict(from_attributes=True)

class PredictionInput(BaseModel):
    employee_id: Optional[int] = None
    age: int = Field(ge=18, le=100)
    monthly_income: float = Field(ge=0)
    years_at_company: float = Field(ge=0, le=80)
    overtime: str
    job_satisfaction: int = Field(ge=1, le=4)
    work_life_balance: int = Field(ge=1, le=4)
    department: str
    job_role: str
