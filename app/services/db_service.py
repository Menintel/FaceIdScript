import os
import json
from sqlalchemy.orm import Session
from app.database.models import Person, FaceEncoding
from app.config import settings
from typing import List, Optional, Dict, Any

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db

    def add_person(self, name: str, email: Optional[str] = None) -> Person:
        """Add a new person to the database"""
        person = Person(name=name, email=email)
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)
        return person

    def get_person(self, person_id: int) -> Optional[Person]:
        """Get a person by ID"""
        return self.db.query(Person).filter(Person.id == person_id).first()

    def get_person_by_name(self, name: str) -> Optional[Person]:
        """Get a person by name"""
        return self.db.query(Person).filter(Person.name == name).first()

    def add_face_encoding(
        self, 
        person_id: int, 
        encoding: List[float], 
        image_path: str
    ) -> FaceEncoding:
        """Add face encoding for a person"""
        # Convert numpy array to JSON-serializable list
        encoding_list = encoding.tolist() if hasattr(encoding, 'tolist') else encoding
        
        face_encoding = FaceEncoding(
            person_id=person_id,
            encoding=json.dumps(encoding_list),
            image_path=image_path
        )
        
        self.db.add(face_encoding)
        self.db.commit()
        self.db.refresh(face_encoding)
        
        return face_encoding

    def get_all_face_encodings(self) -> List[Dict[str, Any]]:
        """Get all face encodings with person information"""
        results = self.db.query(
            FaceEncoding, 
            Person
        ).join(
            Person, 
            Person.id == FaceEncoding.person_id
        ).all()
        
        encodings = []
        for face_encoding, person in results:
            encodings.append({
                'person_id': person.id,
                'name': person.name,
                'encoding': json.loads(face_encoding.encoding),
                'image_path': face_encoding.image_path
            })
            
        return encodings

    def get_person_encodings(self, person_id: int) -> List[List[float]]:
        """Get all face encodings for a specific person"""
        encodings = self.db.query(FaceEncoding).filter(
            FaceEncoding.person_id == person_id
        ).all()
        
        return [json.loads(enc.encoding) for enc in encodings]

    def delete_person(self, person_id: int) -> bool:
        """Delete a person and all their face encodings"""
        # First delete all face encodings for this person
        self.db.query(FaceEncoding).filter(
            FaceEncoding.person_id == person_id
        ).delete()
        
        # Then delete the person
        result = self.db.query(Person).filter(
            Person.id == person_id
        ).delete()
        
        self.db.commit()
        return result > 0
