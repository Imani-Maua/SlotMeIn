# SlotMeIn

**SlotMeIn** is a FastAPI-based shift scheduling REST API designed to intelligently allocate employees (called **talents**) to shifts while respecting their availability, constraints, and labor regulations.

The system provides a complete backend solution with authentication, database management, and a sophisticated scheduling engine that ensures fair and compliant shift assignments.

> ⚠️ **Note:** This is an MVP and not yet in production.

---

## 📂 Project Structure

The project follows a **Domain-Driven Design (DDD)** approach, organizing code by feature rather than technical layer. This makes the codebase scalable and easier to navigate.

```
├── app/
│   ├── authentication/       # User auth & JWT handling
│   │   ├── routes.py         # Login/Register endpoints
│   │   ├── users/            # User management logic
│   │   └── tokens/           # Token generation & validation
│   ├── config/               # Configuration & Environment variables
│   ├── core/                 # Core Business Logic (Domains)
│   │   ├── talents/            # Employee management (CRUD)
│   │   ├── shift_templates/    # Definitions of shift patterns
│   │   ├── shift_period/       # Time intervals for shifts
│   │   ├── constraints/        # Logic for labor rules & availability
│   │   │   ├── constraint_rules/   # Definitions of rules (e.g., "Max 40h")
│   │   │   └── talent_constraints/ # Assigning rules to specific talents
│   │   └── schedule/           # The Scheduling Engine
│   │       ├── allocator/      # Algorithms for assigning staff
│   │       ├── staffing/       # Staffing requirement logic
│   │       └── routes.py       # Schedule generation endpoints
│   ├── database/             # Database connectivity & Models
│   │   ├── models.py         # SQLModel/SQLAlchemy definitions
│   │   └── database.py       # Asyncpg connection pool
│   └── main.py               # Application Entry Point
├── .env                      # Environment variables (git-ignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ✨ Key Features & Code Explanation

### 1. 🧠 Intelligent Scheduling Engine (`app/core/schedule`)
This is the heart of the application. It uses a constraint-satisfaction approach to assign talents to shifts.
- **Allocator**: The module responsible for iterating through shifts and finding the best candidate.
- **Prioritization**:
  - **Hard Constraints**: Mandatory rules (e.g., "Must have 11h rest").
  - **Scoring**: Talents are scored based on suitability and fairness.
  - **Round Robin**: Used to break ties among equally qualified candidates to ensure fair distribution.

### 2. 🛡️ Constraint System (`app/core/constraints`)
The system manages labor regulations through two layers:
- **Constraint Rules**: Global definitions of rules (e.g., "Daily Work Limit", "Weekly Max Hours").
- **Talent Constraints**: Links specific rules to individual talents, allowing for custom contracts (e.g., a Part-Time employee might have a different weekly max than a Full-Time one).

### 3. � Talent & Shift Management
- **Talents**: Comprehensive profiles including roles, skills, and availability.
- **Shift Templates**: Reusable patterns for shifts (e.g., "Morning Shift", "Night Shift") that can be instantiated across different dates.

### 4. � Authentication & Security (`app/authentication`)
- **JWT (JSON Web Tokens)**: Stateless authentication.
- **Role-Based Access**: Granular permissions (though currently focused on Superusers for the MVP).
- **Password Hashing**: Secure storage using `bcrypt`.

### 5. 💾 Database Architecture (`app/database`)
- **Async PostgreSQL**: Uses `asyncpg` for high-performance, non-blocking database queries.
- **SQLAlchemy 2.0+**: Modern ORM usage for type-safe database interactions.

---

## 🚀 Setup

Follow these instructions to get SlotMeIn running locally.

### 1. Clone the repository

```bash
git clone https://github.com/your-username/slotmein.git
cd slotmein 
```

### 2. Create a virtual environment

We recommend using the standard `.venv` naming convention:

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r app/requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root of the project:

```bash
# Database Configuration
DB_HOST=localhost
DB_NAME=scheduler_db
DB_USER=postgres
DB_PASSWORD=password
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/scheduler_db

# JWT Authentication
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Set up the database

Ensure you have PostgreSQL running and the database created. Then initialize the schema:

```bash
# Using Alembic (if configured)
alembic upgrade head

# OR Programmatically (Dev only)
python -c "import asyncio; from app.database.models import Base; from app.database.database import engine; asyncio.run(Base.metadata.create_all(bind=engine))"
```

### 6. Run the FastAPI server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### 7. Access the API documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI
- **Language**: Python 3.11+
- **Database**: PostgreSQL (Async)
- **ORM**: SQLAlchemy 2.0+
- **Auth**: JWT & OAuth2
- **Testing**: Pytest (Planned)