import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User
from models.pdf import PDF
from models.application import Application
from models.permission import Permission
from schemas.application import ApplicationCreate
from services.auth import get_current_user
from services.ai_service import analyze_application
from config import UPLOAD_DIR

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/pdfs")
def list_available_pdfs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all available PDFs for the user."""
    pdfs = db.query(PDF).order_by(PDF.upload_date.desc()).all()
    result = []
    for p in pdfs:
        # Check if user has permission
        perm = db.query(Permission).filter(
            Permission.user_id == current_user.id,
            Permission.pdf_id == p.id,
        ).first()
        # Check if user has a pending application
        app = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.pdf_id == p.id,
        ).order_by(Application.created_at.desc()).first()

        result.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "upload_date": str(p.upload_date) if p.upload_date else None,
            "has_access": perm is not None,
            "application_status": app.status if app else None,
        })
    return result


@router.post("/apply")
def submit_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit an application requesting access to a PDF."""
    # Check PDF exists
    pdf = db.query(PDF).filter(PDF.id == app_data.pdf_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    # Check if user already has permission
    existing_perm = db.query(Permission).filter(
        Permission.user_id == current_user.id,
        Permission.pdf_id == app_data.pdf_id,
    ).first()
    if existing_perm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have access to this PDF",
        )

    # Check if there's already a pending application
    existing_app = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.pdf_id == app_data.pdf_id,
        Application.status == "pending",
    ).first()
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending application for this PDF",
        )

    # AI Analysis
    ai_result = analyze_application(app_data.application_text)

    # Create application
    new_app = Application(
        user_id=current_user.id,
        pdf_id=app_data.pdf_id,
        application_text=app_data.application_text,
        ai_score=ai_result["score"],
        ai_decision=ai_result["recommendation"],
        status="pending",
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return {
        "message": "Application submitted successfully",
        "application_id": new_app.id,
        "ai_score": ai_result["score"],
        "ai_recommendation": ai_result["recommendation"],
        "ai_analysis": ai_result["analysis"],
    }


@router.get("/applications")
def my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View own applications and their statuses."""
    apps = db.query(Application).filter(
        Application.user_id == current_user.id
    ).order_by(Application.created_at.desc()).all()

    result = []
    for app in apps:
        pdf = db.query(PDF).filter(PDF.id == app.pdf_id).first()
        result.append({
            "id": app.id,
            "pdf_title": pdf.title if pdf else "Deleted",
            "pdf_id": app.pdf_id,
            "application_text": app.application_text,
            "ai_score": app.ai_score,
            "ai_decision": app.ai_decision,
            "status": app.status,
            "admin_decision": app.admin_decision,
            "created_at": str(app.created_at) if app.created_at else None,
        })
    return result


@router.get("/download/{pdf_id}")
def download_pdf(
    pdf_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a PDF if the user has permission."""
    # Check permission
    perm = db.query(Permission).filter(
        Permission.user_id == current_user.id,
        Permission.pdf_id == pdf_id,
    ).first()
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not have permission to download this PDF.",
        )

    pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    file_path = os.path.join(UPLOAD_DIR, pdf.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=file_path,
        filename=f"{pdf.title}.pdf",
        media_type="application/pdf",
    )


@router.get("/view/{pdf_id}")
def view_pdf(
    pdf_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View a PDF in browser if the user has permission."""
    perm = db.query(Permission).filter(
        Permission.user_id == current_user.id,
        Permission.pdf_id == pdf_id,
    ).first()
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    file_path = os.path.join(UPLOAD_DIR, pdf.file_path)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        content_disposition_type="inline",
    )
