from fastapi import APIRouter

from app.business.logic import plugin_status

# Not `/plugins`: that prefix belongs to the plugins themselves
# (`/plugins/<id>/...`), and the host's own surface must not sit inside the
# space it hands out.
router = APIRouter(prefix="/plugin-host")


@router.get("/plugins")
def list_plugin_status() -> list[dict]:
    """Which installed plugins the host actually loaded, and why not when it
    did not (`BUG-088`). The frontend asks before mounting a plugin's screens:
    a refused plugin's `.tsx` is compiled into the app whatever the backend
    decided, so without this its page renders and then fails on calls to
    routes that were never mounted."""
    return plugin_status.get_plugin_status()
