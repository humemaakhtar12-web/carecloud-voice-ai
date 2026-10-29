# CareCloud Voice AI Patient Registration

A Python/FastAPI + SQLite starter for the CareCloud Voice AI assessment. It includes validated patient REST endpoints and a small dashboard. The voice provider still needs to be configured.

## Requirements
- Python 3.10+
- Internet connection for package installation

## Run locally (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload
```
If PowerShell blocks activation, use Command Prompt and run:
```bat
.venv\Scripts\activate.bat
```

Open:
- Dashboard: http://127.0.0.1:8000/
- Interactive API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Endpoints
- `GET /patients` optional filters: `last_name`, `date_of_birth`, `phone_number`
- `GET /patients/{patient_id}`
- `POST /patients`
- `PUT /patients/{patient_id}` partial update
- `DELETE /patients/{patient_id}` soft delete
- `POST /voice/register` validated registration endpoint for a voice provider integration

All normal responses use `{ "data": ..., "error": null }`. FastAPI validation errors use the standard 422 response format.

## Example POST body
Use fictional test data only:
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "date_of_birth": "1990-04-18",
  "sex": "Female",
  "phone_number": "2025550148",
  "email": "jane.doe@example.com",
  "address_line_1": "100 Example Street",
  "city": "Washington",
  "state": "DC",
  "zip_code": "20001",
  "preferred_language": "English"
}
```

## Voice integration plan
1. Create a Vapi assistant and a US inbound number.
2. Configure the assistant to gather all required fields, validate them conversationally, read them back, and obtain explicit confirmation before saving.
3. Add a Vapi server tool/function that calls the deployed API's `POST /voice/register` with the confirmed JSON body.
4. Configure the tool schema to require all mandatory fields and map optional fields where provided.
5. Test the whole call and confirm the new patient appears in `GET /patients` and the dashboard.

Do not expose private API keys in frontend code, GitHub, screenshots, or chat. Configure them as environment variables or hosting secrets. This is a demo only: do not enter real patient data.

## Known limitations / next steps
- Voice provider and live deployment are not configured in this starter.
- SQLite is suitable for a quick demo; check host persistent-volume requirements before deploying.
- Add automated tests and authentication/rate limiting before any non-demo use.
- Optional fields are supported; the voice prompt should offer them after required demographics.
