from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database.db import engine, Base, SessionLocal
from models.user import User, UserRole
from models.pdf import PDF
from models.application import Application
from models.permission import Permission
from services.auth import hash_password
from routers import auth, admin, user, pages

app = FastAPI(title="PDF Access Management System", version="1.0.0")

# Mount static files and most
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user.router)


@app.on_event("startup")
def on_startup():
    """Create tables and seed admin account on startup."""
    Base.metadata.create_all(bind=engine)

    # Seed default admin
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.email == "admin@admin.com").first()
        if not existing_admin:
            admin_user = User(
                name="Admin",
                email="admin@admin.com",
                hashed_password=hash_password("admin123"),
                role=UserRole.admin,
            )
            db.add(admin_user)
            db.commit()
            print("[OK] Default admin account created: admin@admin.com / admin123")
        else:
            print("[INFO] Admin account already exists")
    finally:
        db.close()

