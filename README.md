# Face Recognition API

A RESTful API for face recognition and management using DeepFace and FastAPI.

## Features

- Register new people with multiple face images
- Recognize faces in real-time
- Manage person records and face encodings
- RESTful API with OpenAPI documentation
- SQLite database for storage

## Prerequisites

- Python 3.7+
- pip

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd FaceIdScript
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the project root to override default settings:

```env
# Database
DATABASE_URL=sqlite:///faceid.db

# Face Recognition
FACE_DETECTION_MODEL=opencv
FACE_RECOGNITION_MODEL=Facenet
DISTANCE_METRIC=cosine
THRESHOLD=0.6

# Server
HOST=0.0.0.0
PORT=8000
```

## Running the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## API Endpoints

### Register a New Person

```
POST /api/v1/register
```

**Form Data:**
- `name`: Person's name (required)
- `email`: Person's email (optional)
- `images`: List of face images (10 recommended for better accuracy)

### Recognize a Face

```
POST /api/v1/recognize
```

**Form Data:**
- `image`: Image containing a face to recognize

### Get Person Details

```
GET /api/v1/person/{person_id}
```

### Delete a Person

```
DELETE /api/v1/person/{person_id}
```

## Example Usage

### Register a new person

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'name=John Doe' \
  -F 'email=john@example.com' \
  -F 'images=@/path/to/face1.jpg' \
  -F 'images=@/path/to/face2.jpg'
```

### Recognize a face

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/recognize' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@/path/to/unknown_face.jpg'
```

## Project Structure

```
FaceIdScript/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration settings
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py    # Database models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── face_service.py  # Face recognition logic
│   │   └── db_service.py    # Database operations
│   └── api/
│       ├── __init__.py
│       └── endpoints.py     # API endpoints
├── requirements.txt     # Project dependencies
└── README.md           # This file
```

## License

MIT
