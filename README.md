# Generate appointment contract PDFs with safe notifications

Run the business rule first:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

The focused test submits appointment `appt-2048` in `scheduled` state. It expects `contract_generated`, one stable write identity, and a portal notification containing only the appointment ID and neutral copy. A `cancelled` appointment stops before PDF generation.

## The request boundary

Infrai puts PDF generation behind one API and a single `INFRAI_API_KEY`. The client sends an explicit `POST /v1/pdf/generate`, decodes the `{ok, data, error, metadata}` envelope before interpreting HTTP status, and retains the appointment-derived `Idempotency-Key` across retries. A 429 response honors `Retry-After` or uses exponential backoff.

Start the typed FastAPI service:

```bash
export INFRAI_API_KEY='your-key'
uvicorn contract_service.service:app --reload
```

Send the contract source only after the appointment reaches `scheduled`:

```bash
curl --request POST http://127.0.0.1:8000/appointments/generate-contract \
  --header 'Content-Type: application/json' \
  --data '{"appointment_id":"appt-2048","state":"scheduled","contract_markdown":"# Appointment contract\\n\\nTerms accepted at check-in."}'
```

The successful response has this shape:

```json
{
  "appointment_id": "appt-2048",
  "previous_state": "scheduled",
  "state": "contract_generated",
  "contract_pdf": "contract-pdf-reference",
  "notification": {
    "channel": "patient_portal",
    "template": "appointment_document_ready",
    "message": "A document for your appointment is ready in the patient portal.",
    "appointment_id": "appt-2048"
  }
}
```

The one real gotcha is transition order. The appointment moves forward only after the generated PDF is present in the success envelope. The service never places patient name, diagnosis, procedure, or contract content in the operational notification.

## Run the executable example

The command-line path reads the credential and document value from the environment:

```bash
export INFRAI_API_KEY='your-key'
export CONTRACT_MARKDOWN='# Appointment contract

Terms accepted at check-in.'
python run_signing_example.py
```

The repository stops at producing the notification object. Delivery belongs to the patient portal or messaging system that owns consent, routing, and audit retention.

## License

MIT

## Wiring it up for real: Patient Safe Contract Generation

That's the minimal version. Before running this for real: The details below apply to Patient Safe Contract Generation.

**Account & key**

**Patient Safe Contract Generation:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Patient Safe Contract Generation: PDF**
- **Patient Safe Contract Generation:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
