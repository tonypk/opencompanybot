import json
from workers import WorkerEntrypoint, Response, Request


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
router.add_route("GET", "/api/v1/mcp/tools", list_mcp_tools)


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request) -> Response:
        return await router.dispatch(request)
