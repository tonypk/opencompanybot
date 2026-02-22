import os
import httpx


class CompaniesHouseService:
    BASE_URL = "https://api.company-information.service.gov.uk"
    API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY", "0dc87912-e470-473e-ba51-12d0a19fceb5")

    def __init__(self):
        self.client = httpx.AsyncClient(
            auth=(self.API_KEY, ""),
            timeout=30.0,
        )

    async def incorporate_company(
        self,
        company_name: str,
        company_type: str,
        registered_office_address: dict,
        directors: list[dict],
        shareholders: list[dict],
        sic_codes: list[str],
        authentication_code: str | None = None,
    ) -> dict:
        payload = {
            "company_name": company_name,
            "type": company_type,
            "registered_office_address": registered_office_address,
            "directors": directors,
            "shareholders": shareholders,
            "sic_codes": sic_codes,
        }
        if authentication_code:
            payload["authentication_code"] = authentication_code

        response = await self.client.post(
            f"{self.BASE_URL}/company/incorporation",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def get_company(self, company_number: str) -> dict:
        response = await self.client.get(
            f"{self.BASE_URL}/company/{company_number}",
        )
        response.raise_for_status()
        return response.json()

    async def get_filing_history(self, company_number: str) -> dict:
        response = await self.client.get(
            f"{self.BASE_URL}/company/{company_number}/filing-history",
        )
        response.raise_for_status()
        return response.json()

    async def search_companies(
        self, query: str, incorporation_type: str | None = None
    ) -> dict:
        params = {"q": query}
        if incorporation_type:
            params["type"] = incorporation_type

        response = await self.client.get(
            f"{self.BASE_URL}/search/companies",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
