import re
import uuid
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "patients.db"

app = FastAPI(title="CareCloud Voice AI Patient Registration API", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            sex TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT,
            address_line_1 TEXT NOT NULL,
            address_line_2 TEXT,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip_code TEXT NOT NULL,
            insurance_provider TEXT,
            insurance_member_id TEXT,
            preferred_language TEXT NOT NULL DEFAULT 'English',
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT
        )
    """)
    conn.commit()
    return conn


def envelope(data=None, error=None):
    return {"data": data, "error": error}


def row_to_dict(row):
    return dict(row) if row else None


class PatientCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    date_of_birth: date
    sex: str
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str = Field(min_length=1, max_length=200)
    address_line_2: Optional[str] = Field(default=None, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    state: str
    zip_code: str
    insurance_provider: Optional[str] = Field(default=None, max_length=100)
    insurance_member_id: Optional[str] = Field(default=None, max_length=100)
    preferred_language: str = Field(default="English", max_length=50)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=120)
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value):
        if not re.fullmatch(r"[A-Za-z][A-Za-z '-]{0,49}", value):
            raise ValueError("Use letters, spaces, hyphens, or apostrophes only")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value):
        if value >= date.today():
            raise ValueError("Date of birth must be in the past")
        return value

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, value):
        allowed = {"Male", "Female", "Other", "Decline to Answer"}
        match = next((x for x in allowed if x.lower() == value.lower()), None)
        if not match:
            raise ValueError("Must be Male, Female, Other, or Decline to Answer")
        return match

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_us_phone(cls, value):
        if value is None:
            return value
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            raise ValueError("Enter a valid US 10-digit phone number")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, value):
        if not re.fullmatch(r"[A-Za-z]{2}", value):
            raise ValueError("State must be a 2-letter US abbreviation")
        return value.upper()

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, value):
        if not re.fullmatch(r"\d{5}(?:-\d{4})?", value):
            raise ValueError("ZIP must be 5 digits or ZIP+4")
        return value


class PatientUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = Field(default=None, min_length=1, max_length=200)
    address_line_2: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = Field(default=None, max_length=100)
    insurance_member_id: Optional[str] = Field(default=None, max_length=100)
    preferred_language: Optional[str] = Field(default=None, max_length=50)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=120)
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value):
        if value is not None and not re.fullmatch(r"[A-Za-z][A-Za-z '-]{0,49}", value):
            raise ValueError("Use letters, spaces, hyphens, or apostrophes only")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value):
        if value is not None and value >= date.today():
            raise ValueError("Date of birth must be in the past")
        return value

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, value):
        if value is None:
            return value
        allowed = {"Male", "Female", "Other", "Decline to Answer"}
        match = next((x for x in allowed if x.lower() == value.lower()), None)
        if not match:
            raise ValueError("Must be Male, Female, Other, or Decline to Answer")
        return match

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_us_phone(cls, value):
        if value is None:
            return value
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            raise ValueError("Enter a valid US 10-digit phone number")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, value):
        if value is not None and not re.fullmatch(r"[A-Za-z]{2}", value):
            raise ValueError("State must be a 2-letter US abbreviation")
        return value.upper() if value else value

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, value):
        if value is not None and not re.fullmatch(r"\d{5}(?:-\d{4})?", value):
            raise ValueError("ZIP must be 5 digits or ZIP+4")
        return value


@app.on_event("startup")
def startup():
    connect().close()


@app.get("/")
def dashboard():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health():
    return envelope({"status": "ok"})


@app.get("/patients")
def list_patients(
    last_name: Optional[str] = None,
    date_of_birth: Optional[date] = None,
    phone_number: Optional[str] = None,
):
    sql = "SELECT * FROM patients WHERE deleted_at IS NULL"
    params = []
    if last_name:
        sql += " AND lower(last_name) = lower(?)"
        params.append(last_name.strip())
    if date_of_birth:
        sql += " AND date_of_birth = ?"
        params.append(date_of_birth.isoformat())
    if phone_number:
        digits = re.sub(r"\D", "", phone_number)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            raise HTTPException(422, detail="phone_number must be a valid US phone number")
        sql += " AND phone_number = ?"
        params.append(digits)
    sql += " ORDER BY created_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return envelope([row_to_dict(r) for r in rows])


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM patients WHERE patient_id = ? AND deleted_at IS NULL",
            (patient_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, detail="Patient not found")
    return envelope(row_to_dict(row))


@app.post("/patients", status_code=201)
def create_patient(patient: PatientCreate):
    payload = patient.model_dump(mode="json")
    now = utc_now()
    patient_id = str(uuid.uuid4())
    fields = list(payload.keys())
    values = [payload[k] for k in fields]
    columns = ["patient_id"] + fields + ["created_at", "updated_at"]
    placeholders = ", ".join(["?"] * len(columns))
    with connect() as conn:
        conn.execute(
            f"INSERT INTO patients ({', '.join(columns)}) VALUES ({placeholders})",
            [patient_id] + values + [now, now]
        )
        row = conn.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
    print(f"PATIENT_CREATED payload={row_to_dict(row)}", flush=True)
    return envelope(row_to_dict(row))


@app.put("/patients/{patient_id}")
def update_patient(patient_id: str, patient: PatientUpdate):
    updates = patient.model_dump(exclude_unset=True, mode="json")
    if not updates:
        raise HTTPException(400, detail="Provide at least one field to update")
    updates = {k: v for k, v in updates.items() if v is not None}
    if not updates:
        raise HTTPException(400, detail="Provide at least one non-null field to update")
    updates["updated_at"] = utc_now()
    assignments = ", ".join(f"{k} = ?" for k in updates)
    with connect() as conn:
        exists = conn.execute(
            "SELECT patient_id FROM patients WHERE patient_id = ? AND deleted_at IS NULL",
            (patient_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, detail="Patient not found")
        conn.execute(
            f"UPDATE patients SET {assignments} WHERE patient_id = ?",
            list(updates.values()) + [patient_id]
        )
        row = conn.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
    return envelope(row_to_dict(row))


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: str):
    with connect() as conn:
        exists = conn.execute(
            "SELECT patient_id FROM patients WHERE patient_id = ? AND deleted_at IS NULL",
            (patient_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, detail="Patient not found")
        now = utc_now()
        conn.execute(
            "UPDATE patients SET deleted_at = ?, updated_at = ? WHERE patient_id = ?",
            (now, now, patient_id)
        )
    return envelope({"patient_id": patient_id, "deleted_at": now})


# Vapi can call this endpoint after the caller confirms the captured details.
@app.post("/voice/register")
def voice_register(patient: PatientCreate):
    return create_patient(patient)
