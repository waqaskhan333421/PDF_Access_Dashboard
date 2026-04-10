import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User
from models.pdf import PDF
from models.application import Application
from models.permission import Permission
from services.auth import require_admin
from config import UPLOAD_DIR

router = APIRouter(prefix="/admin", tags=["Admin"])
#the real one is the 

# ==================== PDF Management ====================

@router.post("/upload")
def upload_pdf(
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Upload a PDF file (admin only)."""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save file
    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    # Save metadata
    new_pdf = PDF(
        title=title,
        description=description,
        file_path=unique_name,
        uploaded_by=admin.id,
    )
    db.add(new_pdf)
    db.commit()
    db.refresh(new_pdf)

    return {"message": "PDF uploaded successfully", "pdf_id": new_pdf.id}


@router.get("/pdfs")
def list_pdfs(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all uploaded PDFs (admin only)."""
    pdfs = db.query(PDF).order_by(PDF.upload_date.desc()).all()
    result = []
    for p in pdfs:
        result.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "upload_date": str(p.upload_date) if p.upload_date else None,
            "uploaded_by": p.uploaded_by,
        })
    return result


@router.delete("/pdfs/{pdf_id}")
def delete_pdf(
    pdf_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a PDF and its file (admin only)."""
    pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    # Delete file from disk
    file_path = os.path.join(UPLOAD_DIR, pdf.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete related records
    db.query(Permission).filter(Permission.pdf_id == pdf_id).delete()
    db.query(Application).filter(Application.pdf_id == pdf_id).delete()
    db.query(PDF).filter(PDF.id == pdf_id).delete()
    db.commit()

    return {"message": "PDF deleted successfully"}


# ==================== Application Review ====================

@router.get("/applications")
def list_applications(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all applications with user and PDF details (admin only)."""
    apps = db.query(Application).order_by(Application.created_at.desc()).all()
    result = []
    for app in apps:
        user = db.query(User).filter(User.id == app.user_id).first()
        pdf = db.query(PDF).filter(PDF.id == app.pdf_id).first()
        result.append({
            "id": app.id,
            "user_name": user.name if user else "Unknown",
            "user_email": user.email if user else "Unknown",
            "pdf_title": pdf.title if pdf else "Deleted",
            "pdf_id": app.pdf_id,
            "application_text": app.application_text,
            "ai_score": app.ai_score,
            "ai_decision": app.ai_decision,
            "admin_decision": app.admin_decision,
            "status": app.status,
            "created_at": str(app.created_at) if app.created_at else None,
        })
    return result


@router.post("/applications/{app_id}/decide")
def decide_application(
    app_id: int,
    decision: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve or reject an application (admin only)."""
    if decision not in ("approve", "reject"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approve' or 'reject'",
        )

    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.admin_decision = decision
    app.status = "approved" if decision == "approve" else "rejected"

    # If approved, grant permission
    if decision == "approve":
        existing_perm = db.query(Permission).filter(
            Permission.user_id == app.user_id,
            Permission.pdf_id == app.pdf_id,
        ).first()
        if not existing_perm:
            perm = Permission(user_id=app.user_id, pdf_id=app.pdf_id)
            db.add(perm)

    db.commit()
    return {"message": f"Application {decision}d successfully"}


# ==================== User Management ====================

@router.get("/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all users (admin only)."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value if u.role else "user",
            "created_at": str(u.created_at) if u.created_at else None,
        })
    return result


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a user (admin only). Cannot delete yourself."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete related records
    db.query(Permission).filter(Permission.user_id == user_id).delete()
    db.query(Application).filter(Application.user_id == user_id).delete()
    db.query(User).filter(User.id == user_id).delete()
    db.commit()

    return {"message": "User deleted successfully"}
