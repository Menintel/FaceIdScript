from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
from pathlib import Path

from app.database.models import Person, FaceEncoding, get_db
from app.services.face_service import FaceService
from app.services.db_service import DatabaseService
from sqlalchemy.orm import Session
from app.config import settings

router = APIRouter()

def get_face_service(db: Session = Depends(get_db)) -> FaceService:
    """Dependency to get FaceService instance"""
    db_service = DatabaseService(db)
    return FaceService(db_service)

@router.post("/register")
async def register_person(
    name: str = Form(...),
    email: Optional[str] = Form(None),
    images: List[UploadFile] = File(...),
    face_service: FaceService = Depends(get_face_service)
):
    """
    Register a new person with multiple face images
    
    Args:
        name: Name of the person
        email: Email of the person (optional)
        images: List of face images (10 images recommended for better accuracy)
    """
    try:
        # Save uploaded images to temporary files
        temp_paths = []
        for img in images:
            # Validate file type
            if not img.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise HTTPException(status_code=400, detail="Only .png, .jpg and .jpeg files are allowed")
            
            # Create a temporary file
            file_ext = Path(img.filename).suffix
            temp_file = f"/tmp/{uuid.uuid4()}{file_ext}"
            
            # Save the uploaded file
            with open(temp_file, "wb") as buffer:
                buffer.write(await img.read())
                
            temp_paths.append(temp_file)
        
        # Register the person with the face service
        result = face_service.register_person(name, temp_paths, email)
        
        # Clean up temporary files
        for path in temp_paths:
            try:
                os.remove(path)
            except:
                pass
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return {"status": "success", "person_id": result["person_id"], "name": name}
        
    except Exception as e:
        # Clean up any temporary files if an error occurs
        for path in temp_paths:
            try:
                os.remove(path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recognize")
async def recognize_face(
    image: UploadFile = File(...),
    face_service: FaceService = Depends(get_face_service)
):
    """
    Recognize a face in the provided image
    
    Args:
        image: Image containing a face to recognize
    """
    try:
        # Validate file type
        if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="Only .png, .jpg and .jpeg files are allowed")
        
        # Create a temporary file
        file_ext = Path(image.filename).suffix
        temp_file = f"/tmp/{uuid.uuid4()}{file_ext}"
        
        # Save the uploaded file
        with open(temp_file, "wb") as buffer:
            buffer.write(await image.read())
        
        # Recognize the face
        result = face_service.recognize_face(temp_file)
        
        # Clean up
        try:
            os.remove(temp_file)
        except:
            pass
        
        if result["status"] == "no_face":
            return {"status": "no_face", "message": "No face detected in the image"}
            
        if not result.get("recognized", False):
            return {"status": "unknown_face", "message": "Face not recognized"}
            
        return {
            "status": "success",
            "person": result["person"],
            "confidence": result["person"]["confidence"]
        }
        
    except Exception as e:
        # Clean up temporary file if an error occurs
        try:
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/person/{person_id}")
async def get_person(
    person_id: int,
    db: Session = Depends(get_db)
):
    """
    Get person details by ID
    """
    db_service = DatabaseService(db)
    person = db_service.get_person(person_id)
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
        
    # Get all face encodings for this person
    encodings = db_service.get_person_encodings(person_id)
    
    return {
        "id": person.id,
        "name": person.name,
        "email": person.email,
        "face_count": len(encodings),
        "created_at": person.created_at
    }

@router.delete("/person/{person_id}")
async def delete_person(
    person_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a person and all their face encodings
    """
    db_service = DatabaseService(db)
    success = db_service.delete_person(person_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Person not found")
        
    return {"status": "success", "message": "Person deleted successfully"}
