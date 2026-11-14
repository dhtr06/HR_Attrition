from sqlalchemy import String,Integer,Numeric,DateTime,ForeignKey,func
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
class Employee(Base):
 __tablename__='employees'
 id:Mapped[int]=mapped_column(Integer,primary_key=True)
 employee_code:Mapped[str]=mapped_column(String(30),unique=True,index=True)
 full_name:Mapped[str]=mapped_column(String(150))
 age:Mapped[int|None]=mapped_column(Integer,nullable=True)
 department:Mapped[str|None]=mapped_column(String(100),nullable=True)
 job_role:Mapped[str|None]=mapped_column(String(100),nullable=True)
 monthly_income:Mapped[float|None]=mapped_column(Numeric(12,2),nullable=True)
 years_at_company:Mapped[float|None]=mapped_column(Numeric(5,2),nullable=True)
 overtime:Mapped[str|None]=mapped_column(String(10),nullable=True)
 job_satisfaction:Mapped[int|None]=mapped_column(Integer,nullable=True)
 work_life_balance:Mapped[int|None]=mapped_column(Integer,nullable=True)
 created_at:Mapped[object]=mapped_column(DateTime,server_default=func.now())
class PredictionHistory(Base):
 __tablename__='prediction_history'
 id:Mapped[int]=mapped_column(Integer,primary_key=True)
 employee_id:Mapped[int|None]=mapped_column(ForeignKey('employees.id',ondelete='SET NULL'),nullable=True)
 probability:Mapped[float]=mapped_column(Numeric(7,6))
 risk_level:Mapped[str]=mapped_column(String(20))
 model_name:Mapped[str|None]=mapped_column(String(100),nullable=True)
 created_at:Mapped[object]=mapped_column(DateTime,server_default=func.now())
