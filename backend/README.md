## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Monnas
```

### 2. Create Venv Environment

```bash
python3.10 -m venv venv/
```

In Windows:

```bash
venv/Scripts/Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Note: for FastAPI
```bash
pip install "fastapi[standard]"
```
### 4. Install MongoDB

## Run Backend app

### One terminal for FastAPI

```bash
python server.py
```

### FastAPI Swagger UI at

```bash
localhost:8000/docs
```

## Folder Structure (Simplified)

```
backend/
├── api/
├── core/
├── crud/
├── db/
├── models/
├── services/
├── main.py
├── server.py
├── requirements.txt
└── README.md
```