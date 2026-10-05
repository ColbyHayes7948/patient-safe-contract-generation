from enum import StrEnum

from pydantic import BaseModel, Field


class AppointmentState(StrEnum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    CONTRACT_GENERATED = "contract_generated"


class GenerateContractRequest(BaseModel):
    appointment_id: str = Field(min_length=1, max_length=100)
    state: AppointmentState
    contract_markdown: str = Field(min_length=1)


class PatientNotification(BaseModel):
    channel: str
    template: str
    message: str
    appointment_id: str


class GenerateContractResponse(BaseModel):
    appointment_id: str
    previous_state: AppointmentState
    state: AppointmentState
    contract_pdf: str
    notification: PatientNotification
