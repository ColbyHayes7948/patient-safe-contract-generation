import pytest

from contract_service.models import AppointmentState, GenerateContractRequest
from contract_service.signing_workflow import AppointmentConflict, generate_appointment_contract


def contract_request(state: AppointmentState) -> GenerateContractRequest:
    return GenerateContractRequest(
        appointment_id="appt-2048",
        state=state,
        contract_markdown="# Appointment contract\n\nTerms accepted at check-in.",
    )


def test_scheduled_contract_advances_state_and_builds_safe_notification() -> None:
    calls: list[dict[str, object]] = []

    def generator(**payload: object) -> dict[str, str]:
        calls.append(payload)
        return {"url": "contract-pdf-reference"}

    result = generate_appointment_contract(
        contract_request(AppointmentState.SCHEDULED), generator
    )

    assert result.state is AppointmentState.CONTRACT_GENERATED
    assert result.contract_pdf == "contract-pdf-reference"
    assert result.notification.model_dump() == {
        "channel": "patient_portal",
        "template": "appointment_document_ready",
        "message": "A document for your appointment is ready in the patient portal.",
        "appointment_id": "appt-2048",
    }
    assert calls[0]["idempotency_key"] == "appointment-contract:appt-2048"


def test_cancelled_appointment_stops_before_generation() -> None:
    called = False

    def generator(**payload: object) -> dict[str, str]:
        nonlocal called
        called = True
        return {"pdf": "unused"}

    with pytest.raises(AppointmentConflict):
        generate_appointment_contract(contract_request(AppointmentState.CANCELLED), generator)
    assert called is False
