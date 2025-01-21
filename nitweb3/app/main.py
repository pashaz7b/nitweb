from datetime import datetime, date
from loguru import logger
from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated, ClassVar, List
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from app.database_con.database import SessionLocal, engine
from app.model import models
from app.schema.schema import (TeamModel,
                               TeamBase,
                               EmployeeBase,
                               EmployeeModel,
                               EmployeeTeamUpdate,
                               UserCredentials,
                               EmployeeAttendanceLogModel,
                               EmployeeAttendanceLog,
                               EmployeeDailyLeaveRecordModel,
                               EmployeeDailyLeaveRecord,
                               EmployeeHourlyLeaveRecordModel,
                               EmployeeHourlyLeaveRecord,
                               AdminSchema)
from passlib.context import CryptContext
from app.log_conf.log_conf import configure_logger
import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://nitweb.localhost/admin/login", scheme_name="AdminOAuth")
employee_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://nitweb.localhost/employee/login",
                                              scheme_name="EmployeeOAuth")

configure_logger()

app = FastAPI()

origins = [
    # "http://localhost",
    # "http://localhost:5173",
    # "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

models.Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "cfc310c9a91a56446efaf073647dd38054bf7e8104a758f57ff57c346f7c2afb"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    logger.info(f"{to_encode=}")
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_admin(db: Session = Depends(get_db), token: str = Depends(admin_oauth2_scheme)):
    logger.info(f"Checking if token is valid {token}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    if admin is None:
        raise credentials_exception
    return admin


async def get_current_employee(db: Session = Depends(get_db), token: str = Depends(employee_oauth2_scheme)):
    logger.info(f"Checking if token is valid {token}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    employee = db.query(models.Employee).filter(models.Employee.username == username).first()
    if employee is None:
        raise credentials_exception
    return employee


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/admin/register")
async def register_admin(admin: AdminSchema, db: Session = Depends(get_db)):
    db_admin = db.query(models.Admin).filter(models.Admin.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = hash_password(admin.password)
    new_admin = models.Admin(username=admin.username, password=hashed_password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"msg": "Admin registered successfully"}


@app.post("/admin/login")
async def login_admin(admin: Annotated[OAuth2PasswordRequestForm, Depends()],
                      db: Session = Depends(get_db)):
    db_admin = db.query(models.Admin).filter(models.Admin.username == admin.username).first()

    if db_admin is None or not verify_password(admin.password, db_admin.password):
        raise HTTPException(status_code=404, detail="Username or password incorrect")

    access_token = create_access_token(data={"sub": db_admin.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/admin/get_all_teams")
async def get_all_teams(db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
    logger.info("current_admin: " + str(current_admin))
    logger.info("Fetching all teams from the database.")
    teams = db.query(models.Team).all()

    if not teams:
        logger.warning("No teams found in the database.")
        raise HTTPException(status_code=404, detail="No teams found.")

    logger.info(f"Found {len(teams)} teams.")
    return teams


@app.post("/admin/create_team", response_model=TeamModel)
async def create_team(team: TeamBase, db: Session = Depends(get_db),
                      current_admin: models.Admin = Depends(get_current_admin)):
    logger.info(f"Creating a new team with name: {team.team_name}.")
    db_team = models.Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    logger.info(f"Successfully created team with ID: {db_team.team_id}.")

    return db_team


@app.get("/admin/get_team/{team_id}", response_model=TeamModel)
async def get_team_by_id(team_id: int, db: Session = Depends(get_db),
                         current_admin: models.Admin = Depends(get_current_admin)):
    logger.info(f"Fetching team with ID: {team_id}.")
    team = db.query(models.Team).filter(models.Team.team_id == team_id).first()
    if not team:
        logger.warning(f"Team with ID {team_id} not found.")
        raise HTTPException(status_code=404, detail="تیم مدنظر پیدا نشد.")

    logger.info(f"Found team with ID: {team.team_id}.")
    return team


@app.get("/admin/get_all_employees/")
async def get_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                        current_admin: models.Admin = Depends(get_current_admin)):
    logger.info(f"Fetching employees with skip={skip} and limit={limit}.")
    employees = db.query(models.Employee).offset(skip).limit(limit).all()

    if not employees:
        logger.warning("No employees found in the database.")
        raise HTTPException(status_code=404, detail="No employees found.")

    logger.info(f"Found {len(employees)} employees.")

    employees_without_password = [
        {key: value for key, value in employee.__dict__.items() if key != "password"}
        for employee in employees
    ]

    return employees_without_password


@app.get("/admin/get_employee/{employee_id}")
async def get_employee(employee_id: int, db: Session = Depends(get_db),
                       current_admin: models.Admin = Depends(get_current_admin)):
    logger.info(f"Fetching employee with ID: {employee_id}.")
    employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if employee is None:
        logger.warning(f"Employee with ID {employee_id} not found.")
        raise HTTPException(status_code=404, detail="کارمند مدنظر یافت نشد.")

    logger.info(f"Found employee with ID: {employee.employee_id}.")
    employee_without_password = {
        key: value for key, value in employee.__dict__.items() if key != "password"
    }

    return employee_without_password


@app.post("/employee/register", response_model=int)
async def create_emp(emp: EmployeeBase, db: Session = Depends(get_db)):
    logger.info(f" Creating new employee with name{emp.first_name} {emp.last_name}")
    team = db.query(models.Team).filter(models.Team.team_id == emp.team_id).first()
    if not team:
        logger.warning(f"Team with ID {emp.team_id} not found.")
        raise HTTPException(status_code=404, detail="تیمی با آیدی وارد شده یافت نشد.")

    existing_user = db.query(models.Employee).filter(models.Employee.username == emp.username).first()
    if existing_user:
        logger.warning(f"Username {emp.username} already exists.")
        raise HTTPException(status_code=400, detail="نام کاربری تکراری است.")

    hashed_password = hash_password(emp.password)
    db_employee = models.Employee(**emp.dict())
    db_employee.password = hashed_password
    db.add(db_employee)

    team.total_members += 1
    db.commit()
    db.refresh(db_employee)
    db.refresh(team)
    logger.info(f"Successfully created employee {emp.username} with ID {db_employee.employee_id}.")

    return db_employee.employee_id


@app.put("/employee/{employee_id}/update-team", response_model=dict)
async def update_employee_team(employee_id: int, team_update: EmployeeTeamUpdate, db: Session = Depends(get_db),
                               current_employee: models.Employee = Depends(get_current_employee)):
    logger.info(f"Update employee team for employee with id {employee_id}")
    employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if not employee:
        logger.warning(f"Employee with ID {employee_id} not found.")
        raise HTTPException(status_code=404, detail="کارمندی با آیدی وارده یافت نشد.")

    new_team = db.query(models.Team).filter(models.Team.team_id == team_update.team_id).first()
    if not new_team:
        logger.warning(f"Team with ID {team_update.team_id} not found.")
        raise HTTPException(status_code=404, detail="تیمی یافت نشد.")

    if employee.team_id:
        old_team = db.query(models.Team).filter(models.Team.team_id == employee.team_id).first()
        if old_team:
            old_team.total_members -= 1

    employee.team_id = team_update.team_id
    new_team.total_members += 1

    db.commit()
    db.refresh(employee)
    db.refresh(new_team)
    if employee.team_id and old_team:
        db.refresh(old_team)

    logger.warning(f"Team with ID {team_update.team_id} not found.")
    return {"message": "team updated"}


@app.delete("/admin/delete_employees/{employee_id}")
async def delete_employee(employee_id: int, db: Session = Depends(get_db),
                          current_admin: models.Admin = Depends(get_current_admin)):
    logger.info(f"Deleting employee with id {employee_id}")
    employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if not employee:
        logger.warning(f"Employee with ID {employee_id} not found.")
        raise HTTPException(status_code=404, detail="کارمند یافت نشد.")

    if employee.team_id:
        team = db.query(models.Team).filter(models.Team.team_id == employee.team_id).first()
        if team:
            team.total_members -= 1
            db.commit()
            db.refresh(team)
            logger.info(f"Decreased member count for team {team.team_id}. New count: {team.total_members}.")

    db.delete(employee)
    db.commit()
    logger.info(f"Successfully deleted employee with ID {employee_id}.")

    return {"message": "کارمند با موفقیت حذف شد"}


@app.post("/employee/login")
async def authenticate_user(employee: Annotated[OAuth2PasswordRequestForm, Depends()]
                            , db: Session = Depends(get_db)):
    username = employee.username
    password = employee.password

    logger.info(f"login with username {username} and password {password}")
    user = db.query(models.Employee).filter(models.Employee.username == username).first()
    if not user or not verify_password(password, user.password):
        logger.warning(f"Failed login attempt for username {username}.")
        raise HTTPException(status_code=401, detail="نام کاربری یا پسورد خطا است.")

    logger.info(f"User {username} successfully logged in.")
    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/employee/attendance-log/", response_model=EmployeeAttendanceLogModel)
async def create_employee_attendance_log(log: EmployeeAttendanceLog,
                                         db: Session = Depends(get_db),
                                         current_employee: models.Employee = Depends(get_current_employee)
                                         ):
    logger.info(f"Attempting to create employee attendance for employee {log.employee_id}")
    employee = db.query(models.Employee).filter(models.Employee.employee_id == log.employee_id).first()
    if not employee:
        logger.warning(f"Employee with ID {log.employee_id} not found.")
        raise HTTPException(status_code=404, detail="کارمند مدنظر یافت نشد")

    db_attendance_log = models.EmployeeAttendanceLog(**log.dict())
    db.add(db_attendance_log)
    db.commit()
    db.refresh(db_attendance_log)
    logger.info(f"Successfully created attendance log for employee ID {log.employee_id}.")

    return db_attendance_log


@app.get("/admin/get_attendance-log/range", response_model=List[EmployeeAttendanceLogModel])
async def get_attendance_logs_between_dates(start_date: datetime, end_date: datetime, db: Session = Depends(get_db),
                                            current_admin: models.Admin = Depends(get_current_admin)):
    logger.info(f"Getting attendance logs between {start_date} and {end_date}.")
    logs = db.query(models.EmployeeAttendanceLog).filter(
        models.EmployeeAttendanceLog.time_entry >= start_date,
        models.EmployeeAttendanceLog.time_leave <= end_date
    ).all()

    if not logs:
        logger.warning(f"No attendance logs found between {start_date} and {end_date}.")
        raise HTTPException(status_code=404, detail="No attendance logs found.")

    logger.info(f"Successfully fetched {len(logs)} attendance logs between {start_date} and {end_date}.")
    return logs


@app.post("/employee/daily-leave-record/", response_model=EmployeeDailyLeaveRecordModel)
async def create_employee_daily_leave_record(record: EmployeeDailyLeaveRecord, db: Session = Depends(get_db),
                                             current_employee: models.Employee = Depends(get_current_employee)):
    logger.info(f"creating daily leave record for employee ID {record.employee_id}.")
    employee = db.query(models.Employee).filter(models.Employee.employee_id == record.employee_id).first()
    if not employee:
        logger.warning(f"Employee with ID {record.employee_id} not found.")
        raise HTTPException(status_code=404, detail="کارمند مدنظر یافت نشد")

    db_record = models.EmployeeDailyLeaveRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    logger.info(f"Successfully created daily leave record for employee ID {record.employee_id}.")

    return db_record


@app.get("/admin/get_daily-leave-record/range", response_model=List[EmployeeDailyLeaveRecordModel])
async def get_daily_leave_records_between_dates(start_date: date, end_date: date, db: Session = Depends(get_db),
                                                current_admin: models.Admin = Depends(get_current_admin)):
    logger.info(f"Fetching daily leave records between {start_date} and {end_date}.")
    records = db.query(models.EmployeeDailyLeaveRecord).filter(
        models.EmployeeDailyLeaveRecord.time_started >= start_date,
        models.EmployeeDailyLeaveRecord.time_end <= end_date
    ).all()

    if not records:
        logger.warning(f"No daily leave records found between {start_date} and {end_date}.")
        raise HTTPException(status_code=404, detail="No daily leave records found.")

    logger.info(f"Successfully fetched {len(records)} daily leave records between {start_date} and {end_date}.")
    return records


@app.post("/employee/hourly-leave-record/", response_model=EmployeeHourlyLeaveRecordModel)
async def create_employee_hourly_leave_record(
        record: EmployeeHourlyLeaveRecord,
        db: Session = Depends(get_db),
        current_employee: models.Employee = Depends(get_current_employee)
):
    logger.info(f"creating hourly leave record for employee ID {record.employee_id}.")
    employee = db.query(models.Employee).filter(models.Employee.employee_id == record.employee_id).first()
    if not employee:
        logger.warning(f"Employee with ID {record.employee_id} not found.")
        raise HTTPException(status_code=404, detail="کارمند مدنظر یافت نشد")

    db_attendance_log = models.EmployeeHourlyLeaveRecord(**record.dict())
    db.add(db_attendance_log)
    db.commit()
    db.refresh(db_attendance_log)
    logger.info(f"Successfully created hourly leave record for employee ID {record.employee_id}.")

    return db_attendance_log


@app.get("/admin/get_hourly-leave-record/range", response_model=List[EmployeeHourlyLeaveRecordModel])
async def get_hourly_leave_records_between_dates(start_date: datetime, end_date: datetime,
                                                 db: Session = Depends(get_db),
                                                 current_admin: models.Admin = Depends(get_current_admin)):
    logger.info(f"Fetching hourly leave records between {start_date} and {end_date}.")
    records = db.query(models.EmployeeHourlyLeaveRecord).filter(
        models.EmployeeHourlyLeaveRecord.time_started >= start_date,
        models.EmployeeHourlyLeaveRecord.time_end <= end_date
    ).all()

    if not records:
        logger.warning(f"No hourly leave records found between {start_date} and {end_date}.")
        raise HTTPException(status_code=404, detail="No hourly leave records found.")

    logger.info(f"Successfully fetched {len(records)} hourly leave records between {start_date} and {end_date}.")
    return records
