import json
import os

from contract_service.infrai_pdf import InfraiPdfClient
from contract_service.models import AppointmentState, GenerateContractRequest
from contract_service.signing_workflow import generate_appointment_contract


def main() -> None:
    request = GenerateContractRequest(
        appointment_id=os.environ.get("APPOINTMENT_ID", "appt-demo-2048"),
        state=AppointmentState.SCHEDULED,
        contract_markdown=os.environ["CONTRACT_MARKDOWN"],
    )
    result = generate_appointment_contract(request, InfraiPdfClient().generate)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
