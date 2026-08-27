from fastapi import APIRouter

from app.data_access.registry import loader as registry_loader

router = APIRouter(prefix="/boot-status")


@router.get("")
def get_boot_status() -> dict:
    return registry_loader.get_boot_status()


@router.post("/retry")
async def retry_boot() -> dict:
    """Re-runs the SAME boot() a fixed file broke -- lets the operator fix
    or remove the bad file and try again from the BootScreen without a
    backend restart (operator: "Fail Loud so I can fix or remove")."""
    await registry_loader.boot(mode=registry_loader.get_boot_status()["mode"])
    return registry_loader.get_boot_status()
