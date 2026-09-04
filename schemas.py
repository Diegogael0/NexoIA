from datetime import date, time
from pydantic import BaseModel, EmailStr, Field

class LoginIn(BaseModel):
    login: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CompanyCreate(BaseModel):
    name: str
    business_type: str = "Otro"
    phone: str | None = None
    whatsapp: str | None = None
    plan: str = "Pro"
    agent_name: str = "Sofía"

class CompanyOut(CompanyCreate):
    id: int
    ai_enabled: bool
    model_config = {"from_attributes": True}

class AdminUserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    company_id: int
    role: str = "usuario"
    permissions: list[str] = []

class AdminUserUpdate(BaseModel):
    name: str | None = None
    username: str | None = Field(default=None, min_length=3, max_length=80)
    email: EmailStr | None = None
    company_id: int | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: str | None = None
    permissions: list[str] | None = None
    is_active: bool | None = None

class AdminProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    new_password: str | None = Field(default=None, min_length=8, max_length=72)

class BranchCreate(BaseModel):
    name: str
    open_time: time = time(10,0)
    close_time: time = time(20,0)

class StaffCreate(BaseModel):
    name: str
    alias: str | None = None
    role: str = "Profesional"
    branch_id: int | None = None

class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int = 30
    buffer_minutes: int = 0
    price: float = 0

class ClientCreate(BaseModel):
    name: str
    phone: str
    notes: str | None = None

class AppointmentCreate(BaseModel):
    branch_id: int
    client_id: int
    staff_id: int
    service_id: int
    appointment_date: date
    start_time: time
    origin: str = "Recepción"
    notes: str | None = None
