from __future__ import annotations
from datetime import datetime, date, time
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Date, Time, Numeric, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(160))
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    business_type: Mapped[str] = mapped_column(String(80), default="Otro")
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(30), default="#3568f0")
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(40), nullable=True)
    instagram: Mapped[str | None] = mapped_column(String(160), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(220), nullable=True)
    plan: Mapped[str] = mapped_column(String(40), default="Pro")
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_name: Mapped[str] = mapped_column(String(80), default="Sofía")
    agent_greeting: Mapped[str] = mapped_column(Text, default="Gracias por comunicarte. ¿En qué puedo ayudarte?")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id","company_id", name="uq_user_company"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(40), default="usuario")
    permissions: Mapped[str] = mapped_column(Text, default="[]")

class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    open_time: Mapped[time] = mapped_column(Time, default=time(10,0))
    close_time: Mapped[time] = mapped_column(Time, default=time(20,0))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Staff(Base):
    __tablename__ = "staff"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    alias: Mapped[str | None] = mapped_column(String(80), nullable=True)
    role: Mapped[str] = mapped_column(String(80), default="Profesional")
    present: Mapped[bool] = mapped_column(Boolean, default=False)
    operational_status: Mapped[str] = mapped_column(String(40), default="Ausente")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    buffer_minutes: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class StaffService(Base):
    __tablename__ = "staff_services"
    __table_args__ = (UniqueConstraint("staff_id","service_id", name="uq_staff_service"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180))
    phone: Mapped[str] = mapped_column(String(40), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"), nullable=True)
    no_show_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"))
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="RESTRICT"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"))
    appointment_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(40), default="Confirmada")
    origin: Mapped[str] = mapped_column(String(40), default="Recepción")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CheckEvent(Base):
    __tablename__ = "check_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(20))  # in/out/break_start/break_end
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Integration(Base):
    __tablename__ = "integrations"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(60))  # google_calendar, whatsapp, telephony
    status: Mapped[str] = mapped_column(String(30), default="disconnected")
    external_account: Mapped[str | None] = mapped_column(String(255), nullable=True)
    encrypted_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
