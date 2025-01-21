from app.database_con.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship


class Admin(Base):
    __tablename__ = 'admins'
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(500), nullable=False)


class Team(Base):
    __tablename__ = 'teams'
    team_id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String(50), nullable=False)
    total_members = Column(Integer, nullable=False, default=1)

    # Relationship
    employees = relationship("Employee", back_populates="team", cascade="all, delete-orphan")


class Employee(Base):
    __tablename__ = 'employees'
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.team_id', ondelete="SET NULL"), nullable=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False)
    password = Column(String(500), nullable=False)
    national_code = Column(String(10), nullable=False)
    phone_number = Column(String(11), nullable=False)
    address = Column(String(255), nullable=False)

    # Relationships
    team = relationship("Team", back_populates="employees")
    attendance_logs = relationship("EmployeeAttendanceLog", back_populates="employee", cascade="all, delete-orphan")
    daily_leave_records = relationship("EmployeeDailyLeaveRecord", back_populates="employee",
                                       cascade="all, delete-orphan")
    hourly_leave_records = relationship("EmployeeHourlyLeaveRecord", back_populates="employee",
                                        cascade="all, delete-orphan")


class EmployeeAttendanceLog(Base):
    __tablename__ = 'employee_attendance_log'
    table_id = Column(Integer, primary_key=True, autoincrement=True)
    time_entry = Column(DateTime, nullable=False)
    time_leave = Column(DateTime, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id', ondelete="CASCADE"))

    # Relationship
    employee = relationship("Employee", back_populates="attendance_logs")


class EmployeeDailyLeaveRecord(Base):
    __tablename__ = 'employee_daily_leave_records'
    table_id = Column(Integer, primary_key=True, autoincrement=True)
    time_started = Column(Date, nullable=False)
    time_end = Column(Date, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id', ondelete="CASCADE"))

    # Relationship
    employee = relationship("Employee", back_populates="daily_leave_records")


class EmployeeHourlyLeaveRecord(Base):
    __tablename__ = 'employee_hourly_leave_records'
    table_id = Column(Integer, primary_key=True, autoincrement=True)
    time_started = Column(DateTime, nullable=False)
    time_end = Column(DateTime, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.employee_id', ondelete="CASCADE"))

    # Relationship
    employee = relationship("Employee", back_populates="hourly_leave_records")
