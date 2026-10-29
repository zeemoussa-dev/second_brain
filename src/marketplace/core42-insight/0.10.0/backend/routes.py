"""Insight's HTTP surface. The host mounts it under `/plugins/core42-insight/`.

A customer is named by its Customer note's stem, passed as `?stem=` -- a stem is
free text and does not belong in a path segment.
"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Body, File, HTTPException, Response, UploadFile

from . import export_xlsx
from .insight_service import CustomerNotFound, InsightService
from .sources import SourceMissing, vault_not_ready

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _answered(call):
    """Each failure says who can fix it: a missing plugin (424), the request (400/404)."""
    try:
        return call()
    except SourceMissing as exc:
        raise HTTPException(status_code=424, detail=str(exc)) from exc
    except RuntimeError as exc:
        if vault_not_ready(exc):
            raise HTTPException(status_code=503, headers={"Retry-After": "5"},
                                detail="The vault is still loading after a backend restart -- try again in a "
                                       "moment") from exc
        raise
    except CustomerNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _workbook(name: str, content: bytes) -> Response:
    return Response(content, media_type=XLSX,
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


def build_router(service: InsightService) -> APIRouter:
    router = APIRouter()

    @router.get("/customers")
    def get_customers() -> list[dict]:
        return _answered(service.customers)

    @router.get("/customer-list")
    def get_customer_list() -> list[dict]:
        return _answered(service.customer_list)

    @router.get("/customer-row")
    def get_customer_row(stem: str) -> dict:
        return _answered(lambda: service.customer_row(stem))

    @router.get("/terms")
    def get_terms(stem: str) -> dict:
        return _answered(lambda: service.terms(stem))

    @router.put("/terms")
    def put_terms(stem: str, submitted: dict = Body(...)) -> dict:
        return _answered(lambda: service.save_terms(stem, submitted))

    @router.get("/report")
    def get_report(stem: str) -> dict:
        return _answered(lambda: service.report(stem))

    @router.get("/report.xlsx")
    def get_report_export(stem: str) -> Response:
        report = _answered(lambda: service.report(stem))
        return _workbook(*export_xlsx.customer_workbook(report))

    @router.get("/portfolio")
    def get_portfolio() -> dict:
        return _answered(service.portfolio)

    @router.get("/portfolio.xlsx")
    def get_portfolio_export() -> Response:
        portfolio = _answered(service.portfolio)
        reports = [_answered(lambda stem=row["stem"]: service.report(stem))
                   for row in portfolio["customers"] if not row["parent"]]
        return _workbook(*export_xlsx.portfolio_workbook(portfolio, reports))

    @router.get("/terms/export.json")
    def get_terms_export() -> Response:
        """Every customer's terms, for another machine."""
        name, content = _answered(service.export_terms)
        return Response(content, media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})

    @router.post("/terms/import")
    async def post_terms_import(file: UploadFile = File(...), replace: bool = False) -> dict:
        content = await file.read()
        return _answered(lambda: service.import_terms(content, replace))

    @router.get("/settings")
    def get_settings() -> dict:
        return service.settings()

    return router
