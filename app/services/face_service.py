import os
import cv2
import numpy as np
from deepface import DeepFace
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import uuid
import json

from app.config import settings

class FaceService:
    def __init__(self, db_service):
        self.db_service = db_service
        self.model_name = settings.FACE_RECOGNITION_MODEL
        self.detector_backend = settings.FACE_DETECTION_MODEL
        self.distance_metric = settings.DISTANCE_METRIC
        self.threshold = settings.THRESHOLD
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

    def detect_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect faces in an image and return face locations and encodings"""
        try:
            # Use DeepFace to detect and extract faces
            face_objs = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False
            )
            
            # If no faces found, return empty list
            if not face_objs:
                return []
                
            # If single face is detected, convert to list
            if isinstance(face_objs, dict):
                face_objs = [face_objs]
                
            return face_objs
            
        except Exception as e:
            print(f"Error in detect_faces: {str(e)}")
            return []

    def save_face_image(self, image_data: bytes, person_name: str) -> str:
        """Save face image to disk and return the file path"""
        # Create directory for the person if it doesn't exist
        person_dir = os.path.join(settings.UPLOAD_FOLDER, person_name.lower().replace(" ", "_"))
        os.makedirs(person_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(person_dir, filename)
        
        # Convert bytes to numpy array and save as image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imwrite(filepath, img)
        
        return filepath

    def register_person(self, name: str, image_paths: List[str], email: str = None) -> Dict[str, Any]:
        """Register a new person with multiple face images"""
        # Check if person already exists
        existing_person = self.db_service.get_person_by_name(name)
        if existing_person:
            return {"status": "error", "message": f"Person with name '{name}' already exists"}
        
        # Add person to database
        person = self.db_service.add_person(name=name, email=email)
        
        # Process each image
        saved_paths = []
        for img_path in image_paths:
            # Detect faces in the image
            face_objs = self.detect_faces(img_path)
            
            if not face_objs:
                continue
                
            # Use the first detected face
            face = face_objs[0]
            
            # Save the face encoding to database
            self.db_service.add_face_encoding(
                person_id=person.id,
                encoding=face['embedding'],
                image_path=img_path
            )
            
            saved_paths.append(img_path)
        
        if not saved_paths:
            # If no valid faces found in any image, delete the person record
            self.db_service.delete_person(person.id)
            return {"status": "error", "message": "No valid faces found in any of the provided images"}
            
        return {
            "status": "success",
            "person_id": person.id,
            "name": person.name,
            "saved_images": saved_paths
        }

    def recognize_face(self, image_path: str) -> Dict[str, Any]:
        """Recognize a face in the given image"""
        try:
            # Read the image to verify it's valid
            img = cv2.imread(image_path)
            if img is None:
                return {"status": "error", "message": "Invalid image file"}
                
            # Detect faces in the input image
            face_objs = self.detect_faces(image_path)
            
            if not face_objs:
                return {"status": "no_face", "message": "No faces detected in the image"}
                
            # Get all known face encodings from the database
            known_encodings = self.db_service.get_all_face_encodings()
            
            if not known_encodings:
                return {"status": "no_known_faces", "message": "No known faces in the database"}
                
            # Compare with each known face
            best_match = None
            min_distance = float('inf')
            
            for face in face_objs:
                # Skip if no face was actually detected (DeepFace might return empty results with enforce_detection=False)
                if not face or 'embedding' not in face:
                    continue
                    
                for known in known_encodings:
                    if not known or 'encoding' not in known:
                        continue
                        
                    # Calculate distance between face encodings
                    distance = self._calculate_distance(
                        np.array(face['embedding']),
                        np.array(known['encoding'])
                    )
                    
                    if distance < min_distance and distance <= self.threshold:
                        min_distance = distance
                        best_match = {
                            'person_id': known['person_id'],
                            'name': known['name'],
                            'distance': distance,
                            'face_location': face.get('facial_area', {})
                        }
            
            if best_match:
                confidence = 1 - (best_match['distance'] / self.threshold)
                # Only consider it a match if confidence is above a certain threshold
                if confidence > 0.6:  # 60% confidence threshold
                    return {
                        "status": "success",
                        "recognized": True,
                        "person": {
                            "id": best_match['person_id'],
                            "name": best_match['name'],
                            "confidence": confidence
                        },
                        "face_location": best_match['face_location']
                    }
            
            # If we get here, no good match was found
            return {
                "status": "success",
                "recognized": False,
                "message": "No matching face found in the database"
            }
            
        except Exception as e:
            print(f"Error in recognize_face: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing image: {str(e)}"
            }
    
    def _calculate_distance(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Calculate distance between two face encodings"""
        if self.distance_metric == 'cosine':
            return np.dot(encoding1, encoding2) / (np.linalg.norm(encoding1) * np.linalg.norm(encoding2))
        elif self.distance_metric == 'euclidean':
            return np.linalg.norm(encoding1 - encoding2)
        else:
            # Default to cosine distance
            return np.dot(encoding1, encoding2) / (np.linalg.norm(encoding1) * np.linalg.norm(encoding2))
