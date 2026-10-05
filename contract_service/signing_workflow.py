from collections.abc import Callable
from typing import Any

from .models import (
    AppointmentState,
    PatientNotification,
    GenerateContractRequest,
    GenerateContractResponse,
)


class AppointmentConflict(Exception):
    pass


Generator = Callable[..., dict[str, Any]]


def generate_appointment_contract(
    request: GenerateContractRequest, generator: Generator
) -> GenerateContractResponse:
    if request.state is not AppointmentState.SCHEDULED:
        raise AppointmentConflict("Only a scheduled appointment can receive a contract")

    result = generator(
        markdown=request.contract_markdown,
        page_size="A4",
        orientation="portrait",
        store=True,
        idempotency_key=f"appointment-contract:{request.appointment_id}",
    )
    contract_pdf = result.get("url")
    if not isinstance(contract_pdf, str) or not contract_pdf:
        raise ValueError("Generation result must contain url")

    notification = PatientNotification(
        channel="patient_portal",
        template="appointment_document_ready",
        message="A document for your appointment is ready in the patient portal.",
        appointment_id=request.appointment_id,
    )
    return GenerateContractResponse(
        appointment_id=request.appointment_id,
        previous_state=request.state,
        state=AppointmentState.CONTRACT_GENERATED,
        contract_pdf=contract_pdf,
        notification=notification,
    )
