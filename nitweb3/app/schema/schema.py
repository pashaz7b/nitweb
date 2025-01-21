from pydantic import BaseModel
from datetime import datetime, date


class TeamBase(BaseModel):
    team_name: str
    # team_leader_id: int
    total_members: int = 1


class TeamModel(TeamBase):
    class Config:
        orm_mode = True


class EmployeeBase(BaseModel):
    team_id: int
    first_name: str
    last_name: str
    username: str
    password: str
    national_code: str
    phone_number: str
    address: str


class EmployeeModel(EmployeeBase):
    pass

    class Config:
        orm_mode = True


class UserCredentials(BaseModel):
    username: str
    password: str


class EmployeeAttendanceLog(BaseModel):
    time_entry: datetime
    time_leave: datetime
    employee_id: int


class EmployeeAttendanceLogModel(EmployeeAttendanceLog):
    class Config:
        orm_mode = True


class EmployeeDailyLeaveRecord(BaseModel):
    time_started: date
    time_end: date
    employee_id: int


class EmployeeDailyLeaveRecordModel(EmployeeDailyLeaveRecord):
    class Config:
        orm_mode = True


class EmployeeHourlyLeaveRecord(BaseModel):
    time_started: datetime
    time_end: datetime
    employee_id: int


class EmployeeHourlyLeaveRecordModel(EmployeeHourlyLeaveRecord):
    class Config:
        orm_mode = True


class EmployeeTeamUpdate(BaseModel):
    team_id: int


class AdminSchema(BaseModel):
    username: str
    password: str
