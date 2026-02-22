from app.services.companies_house import CompaniesHouseService
from app.services.ccpayment import CCPaymentService


class MCPTools:
    def __init__(self):
        self.companies_house = CompaniesHouseService()
        self.ccpayment = CCPaymentService()
        self._tools = [
            {
                "name": "register_uk_company",
                "description": "Register a UK company through Companies House",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "Company name"},
                        "company_type": {
                            "type": "string",
                            "default": "private-limited",
                            "enum": ["private-limited", "ltd", "plc"],
                        },
                        "registered_office_address": {
                            "type": "object",
                            "properties": {
                                "address_line_1": {"type": "string"},
                                "address_line_2": {"type": "string"},
                                "locality": {"type": "string"},
                                "region": {"type": "string"},
                                "postal_code": {"type": "string"},
                                "country": {"type": "string", "default": "United Kingdom"},
                            },
                            "required": ["address_line_1", "postal_code", "locality"],
                        },
                        "directors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "date_of_birth": {"type": "string"},
                                    "nationality": {"type": "string"},
                                    "occupation": {"type": "string"},
                                    "address": {"type": "object"},
                                },
                                "required": ["name", "date_of_birth"],
                            },
                        },
                        "shareholders": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "shares": {"type": "number"},
                                    "share_type": {"type": "string"},
                                },
                                "required": ["name", "shares"],
                            },
                        },
                        "sic_codes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Standard Industrial Classification codes",
                        },
                    },
                    "required": ["company_name", "registered_office_address", "directors", "shareholders", "sic_codes"],
                },
            },
            {
                "name": "get_company_status",
                "description": "Get the status of a UK company",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_number": {"type": "string", "description": "Company registration number"},
                    },
                    "required": ["company_number"],
                },
            },
            {
                "name": "search_uk_companies",
                "description": "Search for UK companies by name or number",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "incorporation_type": {
                            "type": "string",
                            "description": "Type of company to filter",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "create_usdt_payment",
                "description": "Create a USDT payment order",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number", "description": "Payment amount in USD"},
                        "network": {
                            "type": "string",
                            "enum": ["ERC20", "TRC20"],
                            "default": "ERC20",
                        },
                        "order_id": {"type": "string", "description": "Unique order ID"},
                        "description": {"type": "string"},
                    },
                    "required": ["amount", "order_id"],
                },
            },
            {
                "name": "verify_payment",
                "description": "Verify payment status for an order",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": "Order ID to verify"},
                    },
                    "required": ["order_id"],
                },
            },
        ]

    def list_tools(self) -> list[dict]:
        return self._tools

    async def execute_tool(self, tool_name: str, parameters: dict) -> dict:
        if tool_name == "register_uk_company":
            return await self.companies_house.incorporate_company(
                company_name=parameters["company_name"],
                company_type=parameters.get("company_type", "private-limited"),
                registered_office_address=parameters["registered_office_address"],
                directors=parameters["directors"],
                shareholders=parameters["shareholders"],
                sic_codes=parameters["sic_codes"],
            )

        elif tool_name == "get_company_status":
            return await self.companies_house.get_company(parameters["company_number"])

        elif tool_name == "search_uk_companies":
            return await self.companies_house.search_companies(
                query=parameters["query"],
                incorporation_type=parameters.get("incorporation_type"),
            )

        elif tool_name == "create_usdt_payment":
            return await self.ccpayment.create_payment(
                amount=parameters["amount"],
                currency="USDT",
                network=parameters.get("network", "ERC20"),
                order_id=parameters["order_id"],
                description=parameters.get("description"),
            )

        elif tool_name == "verify_payment":
            return await self.ccpayment.get_payment_status(parameters["order_id"])

        else:
            raise ValueError(f"Unknown tool: {tool_name}")
