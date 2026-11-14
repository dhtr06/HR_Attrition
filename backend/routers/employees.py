from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from ..database import get_db
from ..models import Employee
from ..schemas import EmployeeCreate, EmployeeUpdate, EmployeeOut
from ..services.employee_importer import import_hr_attrition_csv

router = APIRouter(prefix='/api/employees', tags=['Employees'])

@router.get('', response_model=list[EmployeeOut])
def listing(
    q: str = '',
    department: Optional[str] = None,
    overtime: Optional[str] = None,
    db: Session = Depends(get_db)
):
    stmt = select(Employee)
    if q:
        search_filter = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Employee.full_name.like(search_filter),
                Employee.employee_code.like(search_filter),
                Employee.department.like(search_filter),
                Employee.job_role.like(search_filter)
            )
        )
    if department and department != 'All':
        stmt = stmt.where(Employee.department == department)
    if overtime and overtime != 'All':
        stmt = stmt.where(Employee.overtime == overtime)

    return list(db.scalars(stmt.order_by(Employee.id.desc())).all())

@router.get('/{employee_id}', response_model=EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    obj = db.get(Employee, employee_id)
    if not obj:
        raise HTTPException(404, 'Không tìm thấy nhân viên')
    return obj

@router.post('', response_model=EmployeeOut, status_code=201)
def create(data: EmployeeCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Employee).where(Employee.employee_code == data.employee_code))
    if existing:
        raise HTTPException(409, f'Mã nhân viên "{data.employee_code}" đã tồn tại trong hệ thống')
    obj = Employee(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.put('/{employee_id}', response_model=EmployeeOut)
def update_employee(employee_id: int, data: EmployeeUpdate, db: Session = Depends(get_db)):
    obj = db.get(Employee, employee_id)
    if not obj:
        raise HTTPException(404, 'Không tìm thấy nhân viên để cập nhật')
    
    update_data = data.model_dump(exclude_unset=True)
    if 'employee_code' in update_data and update_data['employee_code'] != obj.employee_code:
        dup = db.scalar(select(Employee).where(Employee.employee_code == update_data['employee_code']))
        if dup:
            raise HTTPException(409, f'Mã nhân viên "{update_data["employee_code"]}" đã được dùng')

    for key, value in update_data.items():
        setattr(obj, key, value)
    
    db.commit()
    db.refresh(obj)
    return obj

@router.delete('/{employee_id}', status_code=204)
def delete(employee_id: int, db: Session = Depends(get_db)):
    obj = db.get(Employee, employee_id)
    if not obj:
        raise HTTPException(404, 'Không tìm thấy nhân viên')
    db.delete(obj)
    db.commit()
    return None

@router.post('/seed', status_code=200)
def seed_employees(db: Session = Depends(get_db)):
    current_count = db.scalar(select(Employee.id).limit(1))
    if current_count:
        return {'message': 'Dữ liệu đã có sẵn, không cần nạp lại.'}
    imported_count = import_hr_attrition_csv(db)
    return {'message': f'Đã nạp thành công {imported_count} hồ sơ từ CSV.'}
