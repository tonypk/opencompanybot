from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.companies_house import CompaniesHouseService

router = APIRouter()
ch_service = CompaniesHouseService()


class CompanyIncorporationRequest(BaseModel):
    company_name: str
    company_type: str = "private-limited"
    registered_office_address: dict
    directors: list[dict]
    shareholders: list[dict]
    sic_codes: list[str]
    authentication_code: str | None = None


class CompanyIncorporationResponse(BaseModel):
    company_number: str
    company_name: str
    incorporation_date: str
    status: str


@router.post("/incorporate", response_model=CompanyIncorporationResponse)
async def incorporate_company(request: CompanyIncorporationRequest):
    try:
        result = await ch_service.incorporate_company(
            company_name=request.company_name,
            company_type=request.company_type,
            registered_office_address=request.registered_office_address,
            directors=request.directors,
            shareholders=request.shareholders,
            sic_codes=request.sic_codes,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{company_number}")
async def get_company(company_number: str):
    try:
        company = await ch_service.get_company(company_number)
        return company
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{company_number}/filing-history")
async def get_filing_history(company_number: str):
    try:
        filings = await ch_service.get_filing_history(company_number)
        return filings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/search")
async def search_companies(query: str, incorporation_type: str | None = None):
    try:
        results = await ch_service.search_companies(query, incorporation_type)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
