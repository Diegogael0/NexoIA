from datetime import datetime, timedelta
import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .config import settings
from .db import Base, engine, get_db, SessionLocal
from .models import User, Company, Membership, Branch, Staff, Service, Client, Appointment
from .schemas import LoginIn, TokenOut, CompanyCreate, CompanyOut, AdminUserCreate, AdminUserUpdate, AdminProfileUpdate, BranchCreate, StaffCreate, ServiceCreate, ClientCreate, AppointmentCreate
from .auth import hash_password, verify_password, create_token, current_user, require_company_access, require_platform_admin

Base.metadata.create_all(bind=engine)

def bootstrap_admin():
    db = SessionLocal()
    try:
        # If an administrator already exists, preserve any username/password changes.
        user = db.query(User).filter(User.is_platform_admin==True).order_by(User.id).first()
        if not user:
            user = db.query(User).filter(
                or_(User.username==settings.admin_username, User.email==settings.admin_email)
            ).first()
        if not user:
            user = User(
                username=settings.admin_username,
                email=settings.admin_email,
                name="Administrador Nexo IA",
                password_hash=hash_password(settings.admin_password),
                is_platform_admin=True,
                is_active=True,
            )
            db.add(user)
            db.commit()
        else:
            user.is_platform_admin = True
            user.is_active = True
            db.commit()
    finally:
        db.close()

bootstrap_admin()

app = FastAPI(title="Nexo IA API", version="0.4.2")
origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "service": "nexo-api", "version":"0.4.2"}

@app.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    key=body.login.strip().lower()
    user=db.query(User).filter(or_(User.username==key, User.email==key)).first()
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    return {"access_token": create_token(user.id)}

@app.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    memberships=db.query(Membership).filter(Membership.user_id==user.id).all()
    companies=[]
    for mem in memberships:
        c=db.get(Company, mem.company_id)
        if c:
            companies.append({
                "id":c.id,"name":c.name,"plan":c.plan,"business_type":c.business_type,
                "role":mem.role,"permissions":json.loads(mem.permissions or "[]")
            })
    return {
        "id":user.id,"name":user.name,"username":user.username,"email":user.email,
        "is_platform_admin":user.is_platform_admin,"companies":companies
    }


@app.put("/admin/profile")
def update_admin_profile(body: AdminProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_platform_admin(user)
    username = body.username.strip().lower()
    email = str(body.email).strip().lower()

    existing_username = db.query(User).filter(User.username==username, User.id!=user.id).first()
    if existing_username:
        raise HTTPException(409, "Ese nombre de usuario ya está ocupado")

    existing_email = db.query(User).filter(User.email==email, User.id!=user.id).first()
    if existing_email:
        raise HTTPException(409, "Ese correo ya está registrado")

    user.name = body.name.strip()
    user.username = username
    user.email = email
    if body.new_password:
        user.password_hash = hash_password(body.new_password)

    db.commit()
    return {"ok": True, "username": user.username, "email": user.email, "name": user.name}

@app.post("/companies", response_model=CompanyOut)
def create_company(body: CompanyCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_platform_admin(user)
    company=Company(**body.model_dump())
    db.add(company); db.flush()
    db.add(Branch(company_id=company.id,name="Principal"))
    db.commit(); db.refresh(company)
    return company

@app.get("/companies", response_model=list[CompanyOut])
def list_companies(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.is_platform_admin:
        return db.query(Company).order_by(Company.name).all()
    return db.query(Company).join(Membership,Membership.company_id==Company.id).filter(Membership.user_id==user.id).all()

@app.get("/admin/users")
def admin_users(user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_platform_admin(user)
    rows=[]
    memberships=db.query(Membership).all()
    for mem in memberships:
        u=db.get(User,mem.user_id); c=db.get(Company,mem.company_id)
        if u and c:
            rows.append({
                "id":u.id,"name":u.name,"username":u.username,"email":u.email,
                "is_active":u.is_active,"company_id":c.id,"company_name":c.name,
                "role":mem.role,"permissions":json.loads(mem.permissions or "[]")
            })
    return rows

@app.post("/admin/users")
def create_company_user(body: AdminUserCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_platform_admin(user)
    company=db.get(Company,body.company_id)
    if not company: raise HTTPException(404,"Empresa no encontrada")
    username=body.username.strip().lower()
    email=str(body.email).strip().lower()
    if db.query(User).filter(or_(User.username==username,User.email==email)).first():
        raise HTTPException(409,"El usuario o correo ya existe")
    u=User(username=username,email=email,name=body.name,password_hash=hash_password(body.password),is_active=True)
    db.add(u);db.flush()
    db.add(Membership(user_id=u.id,company_id=company.id,role=body.role,permissions=json.dumps(body.permissions)))
    db.commit();db.refresh(u)
    return {"ok":True,"id":u.id,"username":u.username,"company_id":company.id}

@app.put("/admin/users/{user_id}")
def update_company_user(user_id:int, body:AdminUserUpdate, user:User=Depends(current_user), db:Session=Depends(get_db)):
    require_platform_admin(user)
    u=db.get(User,user_id)
    if not u or u.is_platform_admin: raise HTTPException(404,"Usuario no encontrado")
    mem=db.query(Membership).filter(Membership.user_id==u.id).first()
    if not mem: raise HTTPException(404,"Asignación de empresa no encontrada")

    if body.username is not None:
        username=body.username.strip().lower()
        exists=db.query(User).filter(User.username==username,User.id!=u.id).first()
        if exists: raise HTTPException(409,"Ese nombre de usuario ya está ocupado")
        u.username=username

    if body.email is not None:
        email=str(body.email).strip().lower()
        exists=db.query(User).filter(User.email==email,User.id!=u.id).first()
        if exists: raise HTTPException(409,"Ese correo ya está registrado")
        u.email=email

    if body.company_id is not None:
        company=db.get(Company,body.company_id)
        if not company: raise HTTPException(404,"Empresa no encontrada")
        mem.company_id=company.id

    if body.name is not None: u.name=body.name.strip()
    if body.password: u.password_hash=hash_password(body.password)
    if body.role is not None: mem.role=body.role
    if body.permissions is not None: mem.permissions=json.dumps(body.permissions)
    if body.is_active is not None: u.is_active=body.is_active
    db.commit()
    return {"ok":True,"id":u.id}

def scope(company_id:int,user:User,db:Session):
    require_company_access(company_id,user,db)

@app.post("/companies/{company_id}/branches")
def create_branch(company_id:int,body:BranchCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db)
    obj=Branch(company_id=company_id,**body.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj

@app.get("/companies/{company_id}/staff")
def list_staff(company_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db);return db.query(Staff).filter(Staff.company_id==company_id,Staff.is_active==True).all()

@app.post("/companies/{company_id}/staff")
def create_staff(company_id:int,body:StaffCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db);obj=Staff(company_id=company_id,**body.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj

@app.get("/companies/{company_id}/services")
def list_services(company_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db);return db.query(Service).filter(Service.company_id==company_id,Service.is_active==True).all()

@app.post("/companies/{company_id}/services")
def create_service(company_id:int,body:ServiceCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db);obj=Service(company_id=company_id,**body.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj

@app.get("/companies/{company_id}/clients")
def list_clients(company_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db);return db.query(Client).filter(Client.company_id==company_id).order_by(Client.name).all()

@app.post("/companies/{company_id}/clients")
def create_client(company_id:int,body:ClientCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db);obj=Client(company_id=company_id,**body.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj

@app.get("/companies/{company_id}/appointments")
def list_appointments(company_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db);return db.query(Appointment).filter(Appointment.company_id==company_id).order_by(Appointment.appointment_date,Appointment.start_time).all()

@app.post("/companies/{company_id}/appointments")
def create_appointment(company_id:int,body:AppointmentCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    scope(company_id,user,db)
    service=db.query(Service).filter(Service.id==body.service_id,Service.company_id==company_id).first()
    staff=db.query(Staff).filter(Staff.id==body.staff_id,Staff.company_id==company_id).first()
    client=db.query(Client).filter(Client.id==body.client_id,Client.company_id==company_id).first()
    branch=db.query(Branch).filter(Branch.id==body.branch_id,Branch.company_id==company_id).first()
    if not all([service,staff,client,branch]): raise HTTPException(400,"Algún recurso no pertenece a la empresa")
    start_dt=datetime.combine(body.appointment_date,body.start_time)
    end_time=(start_dt+timedelta(minutes=service.duration_minutes+service.buffer_minutes)).time()
    conflict=db.query(Appointment).filter(
        Appointment.company_id==company_id,Appointment.staff_id==body.staff_id,
        Appointment.appointment_date==body.appointment_date,Appointment.status.notin_(["Cancelada"]),
        Appointment.start_time<end_time,Appointment.end_time>body.start_time
    ).first()
    if conflict: raise HTTPException(409,"El profesional ya tiene una cita en ese horario")
    obj=Appointment(company_id=company_id,end_time=end_time,**body.model_dump())
    db.add(obj);db.commit();db.refresh(obj);return obj
