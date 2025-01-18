from app.database_con.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship


class Team(Base):
    __tablename__ = 'teams'
    team_id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String(50), nullable=False)
    # team_leader_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=True)
    total_members = Column(Integer, nullable=False, default=1)


class Employee(Base):
    __tablename__ = 'employees'
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.team_id'), nullable=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False)
    password = Column(String(500), nullable=False)
    national_code = Column(String(10), nullable=False)
    phone_number = Column(String(11), nullable=False)
    address = Column(String(255), nullable=False)


class EmployeeAttendanceLog(Base):
    __tablename__ = 'employee_attendance_log'
    table_id = Column(Integer, primary_key=True, autoincrement=True)
    time_entry = Column(DateTime, nullable=False)
    time_leave = Column(DateTime, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'))


class EmployeeDailyLeaveRecord(Base):
    __tablename__ = 'employee_daily_leave_records'
    table_id = Column(Integer, primary_key=True, autoincrement=True)
    time_started = Column(Date, nullable=False)
    time_end = Column(Date, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'))


class EmployeeHourlyLeaveRecord(Base):
    __tablename__ = 'employee_hourly_leave_records'
    table_id = Column(Integer, primary_key=True, autoincrement=True)
    time_started = Column(DateTime, nullable=False)
    time_end = Column(DateTime, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'))
