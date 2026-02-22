import json
import os
from workers import WorkerEntrypoint, Response, Request


COMPANIES_HOUSE_API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY", "0dc87912-e470-473e-ba51-12d0a19fceb5")
COMPANIES_HOUSE_URL = "https://api.company-information.service.gov.uk"


class Router:
    def __init__(self):
        self.routes = {}

    def add_route(self, method, path, handler):
        self.routes[(method, path)] = handler

    async def dispatch(self, request):
        from urllib.parse import urlparse
        path = urlparse(request.url).path
        key = (request.method, path)
        if key in self.routes:
            return await self.routes[key](request)
        return Response("Not Found", status=404)


router = Router()


async def health_check(request):
    return Response(
        json.dumps({"status": "healthy", "service": "opencompanybot"}),
        headers={"content-type": "application/json"},
    )


async def root(request):
    return Response(
        json.dumps({
            "name": "OpenCompanyBot API",
            "version": "0.1.0",
            "mcp": "/api/v1/mcp/tools",
        }),
        headers={"content-type": "application/json"},
    )


async def incorporate_company(request):
    try:
        body = await request.json()
    except:
        return Response(
            json.dumps({"error": "Invalid JSON body"}),
            status=400,
            headers={"content-type": "application/json"},
        )

    company_name = body.get("company_name")
    if not company_name:
        return Response(
            json.dumps({"error": "company_name is required"}),
            status=400,
            headers={"content-type": "application/json"},
        )

    payload = json.dumps({
        "company_name": company_name,
        "type": body.get("company_type", "ltd"),
        "registered_office_address": body.get("registered_office_address", {}),
        "directors": body.get("directors", []),
        "shareholders": body.get("shareholders", []),
        "sic_codes": body.get("sic_codes", []),
    })

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {COMPANIES_HOUSE_API_KEY}",
    }

    try:
        ch_response = await fetch(
            f"{COMPANIES_HOUSE_URL}/company/incorporation",
            method="POST",
            headers=headers,
            body=payload,
        )
        
        if ch_response.ok:
            result = await ch_response.json()
            return Response(
                json.dumps({
                    "status": "success",
                    "message": "Company incorporation submitted",
                    "company_name": company_name,
                    "company_number": result.get("company_number", "PENDING"),
                }),
                headers={"content-type": "application/json"},
            )
        else:
            error_text = await ch_response.text()
            return Response(
                json.dumps({
                    "status": "error",
                    "error": "Companies House API error",
                    "details": error_text,
                }),
                status=ch_response.status,
                headers={"content-type": "application/json"},
            )
    except Exception as e:
        return Response(
            json.dumps({
                "status": "error",
                "error": str(e),
            }),
            status=500,
            headers={"content-type": "application/json"},
        )


async def list_mcp_tools(request):
    tools = [
        {
            "name": "register_uk_company",
            "description": "Register a UK company through Companies House",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "company_type": {"type": "string", "default": "private-limited"},
                },
                "required": ["company_name"],
            },
        },
        {
            "name": "get_company_status",
            "description": "Get the status of a UK company",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_number": {"type": "string"},
                },
                "required": ["company_number"],
            },
        },
        {
            "name": "create_usdt_payment",
            "description": "Create a USDT payment order",
            "input_schema": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "network": {"type": "string", "default": "ERC20"},
                    "order_id": {"type": "string"},
                },
                "required": ["amount", "order_id"],
            },
        },
    ]
    return Response(
        json.dumps({"tools": tools}),
        headers={"content-type": "application/json"},
    )


router.add_route("GET", "/health", health_check)
router.add_route("GET", "/", root)
router.add_route("POST", "/api/v1/companies/incorporate", incorporate_company)
router.add_route("GET", "/api/v1/mcp/tools", list_mcp_tools)


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request) -> Response:
        return await router.dispatch(request)
