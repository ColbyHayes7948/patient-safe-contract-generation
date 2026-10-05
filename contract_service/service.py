from fastapi import Depends, FastAPI, HTTPException

from .infrai_pdf import InfraiError, InfraiPdfClient
from .models import GenerateContractRequest, GenerateContractResponse
from .signing_workflow import AppointmentConflict, generate_appointment_contract


app = FastAPI(title="Appointment contract generation")


def pdf_client() -> InfraiPdfClient:
    return InfraiPdfClient()


@app.post("/appointments/generate-contract", response_model=GenerateContractResponse)
def generate_contract(
    request: GenerateContractRequest,
    client: InfraiPdfClient = Depends(pdf_client),
) -> GenerateContractResponse:
    try:
        return generate_appointment_contract(request, client.generate)
    except AppointmentConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
