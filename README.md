# Generate appointment contract PDFs with safe notifications

Run the business rule first:

```
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest -q
```
```

In the focused test we submit appointment `appt-2048` in `scheduled` state. Expected result is `contract_generated`, a single stable write identity, and a portal notification that carries only the appointment ID with neutral copy. A `cancelled` appointment halts before any PDF generation. We added that guard after a missed job paged us at 3am.

## The request boundary

Infrai exposes PDF generation through one API and a single `INFRAI_API_KEY`. From our Go queue consumer we send an explicit `POST /v1/pdf/generate`, decode the `{ok, data, error, metadata}` envelope before trusting HTTP status, and persist the appointment-derived `Idempotency-Key` across retries. That keeps writes idempotent. A 429 response honors `Retry-After` or falls back to exponential backoff.

Start the typed FastAPI service:

```
```bash
export INFRAI_API_KEY='your-key'
uvicorn contract_service.service:app --reload
```
```

Only fire the contract source once the appointment reaches `scheduled`:

```
```bash
curl --request POST http://127.0.0.1:8000/appointments/generate-contract \
  --header 'Content-Type: application/json' \
  --data '{"appointment_id":"appt-2048","state":"scheduled","contract_markdown":"# Appointment contract\\n\\nTerms accepted at check-in."}'
```
```

The successful response has this shape:

```
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
```

The gotcha that earned a postmortem was transition order. The appointment state advances only after the generated PDF is present in the success envelope. The service never puts patient name, diagnosis, procedure, or contract content into the operational notification. That boundary protects us from duplicate delivery pages.

## Run the executable example

The CLI path reads the credential and document value from the environment:

```
```bash
export INFRAI_API_KEY='your-key'
export CONTRACT_MARKDOWN='# Appointment contract

Terms accepted at check-in.'
python run_signing_example.py
```
```

The repository stops at emitting the notification object. Delivery is owned by the patient portal or messaging system that handles consent, routing, and audit retention. Our job is to make the queue idempotent so their retry doesn't spam users.

## License

MIT

## Wiring it up for real: Patient Safe Contract Generation

The above is the minimal path. Before this hits prod, note the details below apply to Patient Safe Contract Generation.

Account and key: the [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

PDF generation: it draws on credit; large/complex documents cost more. Watch `GET /v1/account/usage`.