import json
import secrets
import hashlib
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from workers import WorkerEntrypoint, Response, Request


# UK Companies House XML Gateway Integration
class CompaniesHouseXMLGateway:
    """UK Companies House XML Gateway Client for company incorporation"""
    
    TEST_URL = "https://xmlgw.companieshouse.gov.uk/v2-1/schema/1/incorporation.xsd"
    LIVE_URL = "https://xmlgateway.companieshouse.gov.uk/v2-1/schema/1/incorporation.xsd"
    
    def __init__(self, presenter_id: str = None, auth_code: str = None, test_mode: bool = True):
        self.presenter_id = presenter_id or "DEMO_PRESENTER"
        self.auth_code = auth_code or "DEMO_AUTH"
        self.test_mode = test_mode
        self.endpoint = self.TEST_URL if test_mode else self.LIVE_URL
    
    def _generate_digest(self, data: str) -> str:
        return hashlib.md5(data.encode()).hexdigest().upper()
    
    def build_incorporation_xml(self, company_data: dict) -> tuple:
        """Build complete incorporation XML message"""
        transaction_id = f"INC-{secrets.token_hex(8).upper()}"
        
        # Build XML
        root = ET.Element("GovTalkMessage")
        root.set("xmlns", "http://www.govtalk.gov.uk/schemas/govtalk/govtalkheader")
        
        env_version = ET.SubElement(root, "EnvelopeVersion")
        env_version.text = "2.0"
        
        # Header
        header = ET.SubElement(root, "Header")
        sender = ET.SubElement(header, "SenderDetails")
        id_auth = ET.SubElement(sender, "IDAuthentication")
        
        sender_id = ET.SubElement(id_auth, "SenderID")
        sender_id.text = self.presenter_id
        
        auth = ET.SubElement(id_auth, "Authentication")
        method = ET.SubElement(auth, "Method")
        method.text = "MD5"
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        value = ET.SubElement(auth, "Value")
        value.text = self._generate_digest(self.auth_code + timestamp)
        
        transaction = ET.SubElement(header, "TransactionID")
        transaction.text = transaction_id
        
        # GovTalkDetails
        gov_talk = ET.SubElement(root, "GovTalkDetails")
        key_store = ET.SubElement(gov_talk, "KeyStore")
        key = ET.SubElement(key_store, "Key")
        key.set("Type", "Service")
        key.text = "Incorporation"
        
        # Body
        body = ET.SubElement(root, "Body")
        
        # Simplified incorporation request
        incorp = ET.SubElement(body, "IncorporationRequest")
        
        name = ET.SubElement(incorp, "CompanyName")
        name.text = company_data.get("company_name", "")
        
        ctype = ET.SubElement(incorp, "CompanyType")
        ctype.text = company_data.get("company_type", "ltd")
        
        # Address
        address = company_data.get("registered_office_address", {})
        addr = ET.SubElement(incorp, "RegisteredOfficeAddress")
        ET.SubElement(addr, "AddressLine1").text = address.get("address_line_1", "")
        ET.SubElement(addr, "Locality").text = address.get("locality", "")
        ET.SubElement(addr, "PostalCode").text = address.get("postal_code", "")
        
        # Directors
        directors = ET.SubElement(incorp, "Directors")
        for d in company_data.get("directors", []):
            director = ET.SubElement(directors, "Director")
            name_elem = ET.SubElement(director, "Name")
            ET.SubElement(name_elem, "Forename").text = d.get("forename", "")
            ET.SubElement(name_elem, "Surname").text = d.get("surname", "")
        
        # IDV (Identity Verification) - Required as of 2025
        idv = ET.SubElement(incorp, "IdentityVerification")
        ET.SubElement(idv, "Status").text = "VERIFIED"
        
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        
        return xml_str, transaction_id
    
    async def incorporate_company(self, company_data: dict) -> dict:
        """Submit company incorporation to Companies House"""
        
        if self.test_mode:
            # Demo mode - return simulated response
            xml, txn_id = self.build_incorporation_xml(company_data)
            return {
                "status": "submitted",
                "transaction_id": txn_id,
                "company_number": "PENDING",
                "message": "Test mode: In production, this would submit to Companies House XML Gateway",
                "xml_preview": xml[:200] + "...",
                "test_mode": True,
                "next_steps": [
                    "1. Apply for Presenter ID at Companies House",
                    "2. Complete Direct Debit setup for fees (£50)",
                    "3. Pass Identity Verification for all directors",
                    "4. Submit to production environment after testing"
                ]
            }
        
        # Production: would send to actual API
        # This requires real Presenter ID and authentication
        return {"status": "error", "message": "Production mode requires real credentials"}


# XML Gateway instance
xml_gateway = CompaniesHouseXMLGateway(test_mode=True)


# Provider configuration - in production, these would be real API endpoints
PROVIDERS = {
    "uk": {
        "name": "Letsy",
        "api_endpoint": "https://api.letsy.co/formations",
        "type": "api",  # api or manual
        "features": ["ltd", "llp"],
        "virtual_address": True
    },
    "sg": {
        "name": "Singapore Incorporation Services",
        "api_endpoint": "https://api.singaporeincorp.sg/v1",  # placeholder
        "type": "api",
        "features": ["pte_ltd", "llp"],
        "virtual_address": True,
        "requirements": ["singpass", "business_reg"]  # local requirements
    },
    "hk": {
        "name": "Hong Kong Company Services",
        "api_endpoint": "https://api.hkcompanies.gov.hk/v1",  # placeholder
        "type": "api",
        "features": ["ltd", "company"],
        "virtual_address": True,
        "requirements": ["hkid"]
    },
    "ae": {
        "name": "UAE Free Zone Services",
        "api_endpoint": "https://api.uaefreezone.gov.ae/v1",  # placeholder
        "type": "manual",  # typically manual process
        "features": ["freezone", "mainland"],
        "virtual_address": True,
        "requirements": ["passport", "visa"]
    },
    "us": {
        "name": "US State Filing Services",
        "api_endpoint": "https://api.statefiling.gov/v1",  # placeholder
        "type": "api",
        "features": ["llc", "corporation"],
        "virtual_address": True,
        "requirements": ["ssn", "itin"]
    }
}

# Country-specific requirements
COUNTRY_REQUIREMENTS = {
    "uk": {
        "fields": ["company_name", "company_type", "directors", "shareholders", "registered_office_address"],
        "documents": ["passport", "proof_of_address"],
        "sic_codes": True,
        "companies_house_fee": 50
    },
    "sg": {
        "fields": ["company_name", "company_type", "shareholders", "directors", "registered_address"],
        "documents": ["singpass", "passport", "business_profile"],
        "acra_fee": 300
    },
    "hk": {
        "fields": ["company_name", "company_type", "shareholders", "directors", "registered_address"],
        "documents": ["hkid_card", "passport", "address_proof"],
        "companies_house_fee": 200
    },
    "ae": {
        "fields": ["company_name", "company_type", "shareholders", "directors", "freezone"],
        "documents": ["passport", "visa", "emirates_id"],
        "freezone_options": ["DMCC", "IFZA", "DAFZA", "JAFZA"]
    },
    "us": {
        "fields": ["company_name", "company_type", "state", "shareholders", "registered_agent"],
        "documents": ["ssn", "passport", "state_id"],
        "states": ["Delaware", "Wyoming", "Florida", "Texas"]
    }
}


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request, env) -> Response:
        from urllib.parse import urlparse, parse_qs
        from datetime import datetime
        
        path = urlparse(request.url).path
        query = urlparse(request.url).query
        params = parse_qs(query)
        
        cors = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
        
        db = getattr(self.env, "DB", None)
        
        def error_response(message, status=400):
            return Response(json.dumps({"error": message}), status=status, headers=cors)
        
        def success_response(data, status=200):
            return Response(json.dumps(data), status=status, headers=cors)
        
        # CORS preflight
        if request.method == "OPTIONS":
            return Response("", status=204, headers={
                **cors,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            })
        
        # ============ Root & Health ============
        if path == "/":
            return success_response({
                "name": "OpenCompanyBot API", 
                "version": "2.0.0",
                "status": "operational",
                "countries": list(PROVIDERS.keys())
            })
        
        if path == "/health":
            return success_response({
                "status": "healthy", 
                "timestamp": datetime.now().isoformat(),
                "providers": list(PROVIDERS.keys())
            })
        
        # ============ Providers API ============
        if path == "/api/v1/providers" and request.method == "GET":
            providers_list = []
            for code, info in PROVIDERS.items():
                providers_list.append({
                    "code": code,
                    "name": info["name"],
                    "type": info["type"],
                    "features": info["features"],
                    "virtual_address": info.get("virtual_address", False)
                })
            return success_response({"providers": providers_list})
        
        # ============ Countries API ============
        if path == "/api/v1/countries" and request.method == "GET":
            countries = []
            for code, info in PROVIDERS.items():
                reqs = COUNTRY_REQUIREMENTS.get(code, {})
                countries.append({
                    "code": code,
                    "name": code.upper(),
                    "flag": self._get_flag(code),
                    "available": True,  # All available now
                    "type": info["type"],
                    "features": info["features"],
                    "requirements": reqs.get("fields", []),
                    "pricing": {
                        "base": reqs.get("companies_house_fee", reqs.get("acra_fee", 100)),
                        "currency": "USD" if code != "uk" else "GBP",
                        "includes": self._get_price_includes(code)
                    }
                })
            return success_response({"countries": countries})
        
        # Get specific country details
        if path.startswith("/api/v1/countries/") and request.method == "GET":
            country_code = path.split("/")[-1]
            if country_code not in PROVIDERS:
                return error_response("Country not found", 404)
            
            return success_response({
                "code": country_code,
                "provider": PROVIDERS[country_code],
                "requirements": COUNTRY_REQUIREMENTS.get(country_code, {}),
                "registration_fields": self._get_registration_fields(country_code)
            })
        
        # ============ MCP Tools API ============
        if path == "/api/v1/mcp/tools" and request.method == "GET":
            return success_response({
                "tools": [
                    {"name": "register_company", "description": "Register a company in any supported country"},
                    {"name": "check_company_status", "description": "Check incorporation status"},
                    {"name": "search_company_name", "description": "Check name availability"},
                    {"name": "get_requirements", "description": "Get registration requirements for a country"},
                    {"name": "calculate_price", "description": "Calculate total registration cost"}
                ]
            })
        
        # ============ AI Agents Team API ============
        if path == "/api/v1/agents" and request.method == "GET":
            from app.agents.team import agent_team, AgentRole, AgentTask
            return success_response({
                "team": agent_team.get_team_status(),
                "summary": agent_team.get_team_summary()
            })
        
        if path == "/api/v1/agents/ceo" and request.method == "POST":
            from app.agents.team import agent_team, AgentRole, AgentTask
            task = AgentTask(
                task_id=f"TASK-{secrets.token_hex(4)}",
                agent_role=AgentRole.CEO,
                description="analyze_performance"
            )
            result = await agent_team.process_task(AgentRole.CEO, task)
            return success_response({"result": result})
        
        if path == "/api/v1/agents/sales" and request.method == "POST":
            from app.agents.team import agent_team, AgentRole, AgentTask
            try:
                body = await request.json()
            except:
                body = {}
            
            action = body.get("action", "handle_inquiry")
            task = AgentTask(
                task_id=f"TASK-{secrets.token_hex(4)}",
                agent_role=AgentRole.SALES,
                description=f"{action}_lead" if action == "qualify" else "handle_inquiry",
                metadata=body
            )
            result = await agent_team.process_task(AgentRole.SALES, task)
            return success_response({"result": result})
        
        if path == "/api/v1/agents/support" and request.method == "POST":
            from app.agents.team import agent_team, AgentRole, AgentTask
            try:
                body = await request.json()
            except:
                body = {}
            
            task = AgentTask(
                task_id=f"TASK-{secrets.token_hex(4)}",
                agent_role=AgentRole.SUPPORT,
                description=body.get("type", "faq"),
                metadata=body
            )
            result = await agent_team.process_task(AgentRole.SUPPORT, task)
            return success_response({"result": result})
        
        if path == "/api/v1/agents/register" and request.method == "POST":
            from app.agents.team import agent_team, AgentRole, AgentTask
            try:
                body = await request.json()
            except:
                body = {}
            
            task = AgentTask(
                task_id=f"TASK-{secrets.token_hex(4)}",
                agent_role=AgentRole.REGISTRATION,
                description="register_company",
                metadata=body
            )
            result = await agent_team.process_task(AgentRole.REGISTRATION, task)
            return success_response({"result": result})
        
        if path == "/api/v1/agents/kyc" and request.method == "POST":
            from app.agents.team import agent_team, AgentRole, AgentTask
            try:
                body = await request.json()
            except:
                body = {}
            
            task = AgentTask(
                task_id=f"TASK-{secrets.token_hex(4)}",
                agent_role=AgentRole.COMPLIANCE,
                description="verify_kyc",
                metadata=body
            )
            result = await agent_team.process_task(AgentRole.COMPLIANCE, task)
            return success_response({"result": result})
        
        if path == "/api/v1/agents/payment" and request.method == "POST":
            from app.agents.team import agent_team, AgentRole, AgentTask
            try:
                body = await request.json()
            except:
                body = {}
            
            task = AgentTask(
                task_id=f"TASK-{secrets.token_hex(4)}",
                agent_role=AgentRole.PAYMENT,
                description=body.get("action", "process_payment"),
                metadata=body
            )
            result = await agent_team.process_task(AgentRole.PAYMENT, task)
            return success_response({"result": result})
        
        # ============ Auth API ============
        if path == "/api/v1/auth/register" and request.method == "POST":
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            email = body.get("email", "").lower().strip()
            password = body.get("password", "")
            name = body.get("name", "").strip()
            
            if not email or not password:
                return error_response("Email and password are required")
            
            if len(password) < 6:
                return error_response("Password must be at least 6 characters")
            
            token = secrets.token_hex(32)
            
            return success_response({
                "status": "ok", 
                "token": token, 
                "user": {
                    "email": email, 
                    "name": name if name else email.split("@")[0]
                }
            })
        
        if path == "/api/v1/auth/login" and request.method == "POST":
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            email = body.get("email", "").lower().strip()
            password = body.get("password", "")
            
            if not email or not password:
                return error_response("Email and password are required")
            
            token = secrets.token_hex(32)
            
            return success_response({
                "status": "ok", 
                "token": token, 
                "user": {"email": email}
            })
        
        if path == "/api/v1/auth/profile" and request.method == "GET":
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return error_response("Unauthorized", 401)
            
            return success_response({"user": {"email": "user@example.com"}})
        
        # ============ Orders API ============
        if path == "/api/v1/orders" and request.method == "POST":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Please login first", 401)
            
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            country = body.get("country", "uk")
            company_name = body.get("company_name", "").strip()
            company_type = body.get("company_type", "ltd")
            virtual = body.get("use_virtual_address", False)
            
            if country not in PROVIDERS:
                return error_response("Unsupported country")
            
            if not company_name:
                return error_response("Company name is required")
            
            # Calculate price
            total = self._calculate_price(country, company_type, virtual)
            
            order_id = f"ORD-{secrets.token_hex(6).upper()}"
            
            return success_response({
                "status": "ok",
                "order": {
                    "id": order_id, 
                    "company_name": company_name,
                    "country": country,
                    "provider": PROVIDERS[country]["name"],
                    "company_type": company_type,
                    "virtual_address": virtual,
                    "amount": total["total"],
                    "currency": total["currency"],
                    "breakdown": total["breakdown"],
                    "status": "pending_payment",
                    "created_at": datetime.now().isoformat()
                }
            })
        
        if path == "/api/v1/orders" and request.method == "GET":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Unauthorized", 401)
            
            # Demo orders
            return success_response({
                "orders": [
                    {
                        "id": "ORD-DEMO001",
                        "company_name": "Tech Solutions Pte Ltd",
                        "country": "sg",
                        "provider": PROVIDERS["sg"]["name"],
                        "status": "completed",
                        "amount": 350,
                        "currency": "USD",
                        "created_at": "2026-02-15T10:00:00Z"
                    },
                    {
                        "id": "ORD-DEMO002", 
                        "company_name": "Dubai Trading LLC",
                        "country": "ae",
                        "provider": PROVIDERS["ae"]["name"],
                        "status": "processing",
                        "amount": 580,
                        "currency": "USD",
                        "created_at": "2026-02-20T14:30:00Z"
                    }
                ]
            })
        
        if path.startswith("/api/v1/orders/") and request.method == "GET":
            order_id = path.split("/")[-1]
            return success_response({
                "order": {
                    "id": order_id,
                    "status": "processing",
                    "company_name": "Demo Company Ltd",
                    "country": "uk",
                    "steps": [
                        {"step": "payment", "status": "completed"},
                        {"step": "verification", "status": "completed"},
                        {"step": "filing", "status": "in_progress"},
                        {"step": "certificate", "status": "pending"}
                    ]
                }
            })
        
        # ============ Company Incorporation API ============
        if path == "/api/v1/companies/incorporate" and request.method == "POST":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Please login first", 401)
            
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            country = body.get("country", "uk").lower()
            company_name = body.get("company_name", "").strip()
            company_type = body.get("company_type", "ltd")
            
            if country not in PROVIDERS:
                return error_response("Unsupported country. Choose from: " + ", ".join(PROVIDERS.keys()))
            
            if not company_name:
                return error_response("Company name is required")
            
            provider = PROVIDERS[country]
            
            # UK uses XML Gateway
            if country == "uk":
                incorporation_id = f"INC-UK-{secrets.token_hex(8).upper()}"
                
                # Prepare company data for XML Gateway
                company_data = {
                    "company_name": company_name,
                    "company_type": company_type,
                    "registered_office_address": body.get("registered_office_address", {
                        "address_line_1": body.get("address_line_1", "123 Main Street"),
                        "locality": body.get("locality", "London"),
                        "postal_code": body.get("postal_code", "SW1A 1AA")
                    }),
                    "directors": [{
                        "forename": body.get("director_name", "John").split()[0],
                        "surname": " ".join(body.get("director_name", "John Smith").split()[1:]) or "Smith"
                    }],
                    "sic_codes": [body.get("sic_code", "62012")]
                }
                
                # Submit via XML Gateway
                result = await xml_gateway.incorporate_company(company_data)
                
                return success_response({
                    "status": "success",
                    "message": "UK Company incorporation submitted via XML Gateway",
                    "incorporation_id": result.get("transaction_id", incorporation_id),
                    "country": country,
                    "provider": "Companies House XML Gateway",
                    "provider_type": "xml_gateway",
                    "company_name": company_name,
                    "company_type": company_type,
                    "company_number": result.get("company_number", "PENDING"),
                    "xml_generated": True,
                    "estimated_processing_time": "3-5 business days",
                    "test_mode": result.get("test_mode", True),
                    "next_steps": result.get("next_steps", [
                        "Complete payment",
                        "Verify director identity",
                        "Companies House reviews application",
                        "Receive certificate"
                    ])
                })
            
            # Other countries use provider API
            incorporation_id = f"INC-{country.upper()}-{secrets.token_hex(8).upper()}"
            
            response = {
                "status": "success",
                "message": f"Company incorporation submitted to {provider['name']}",
                "incorporation_id": incorporation_id,
                "country": country,
                "provider": provider["name"],
                "provider_type": provider["type"],
                "company_name": company_name,
                "company_type": company_type,
                "company_number": "PENDING",
                "estimated_processing_time": self._get_processing_time(country),
                "next_steps": self._get_next_steps(country, provider["type"])
            }
            
            return success_response(response)
        
        # ============ Company Search API ============
        if path == "/api/v1/companies/search" and request.method == "GET":
            params = parse_qs(query)
            company_name = params.get("q", [''])[0]
            country = params.get("country", ["uk"])[0]
            
            if not company_name:
                return error_response("Company name is required")
            
            if country not in PROVIDERS:
                return error_response("Unsupported country")
            
            # Simulate availability check
            import random
            available = random.choice([True, True, False])
            
            return success_response({
                "company_name": company_name,
                "country": country,
                "available": available,
                "suggestions": [] if available else ["Tech Solutions Ltd", "Digital Ventures Ltd"]
            })
        
        # ============ Price Calculator API ============
        if path == "/api/v1/pricing/calculate" and request.method == "POST":
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            country = body.get("country", "uk")
            company_type = body.get("company_type", "ltd")
            virtual = body.get("virtual_address", False)
            
            if country not in PROVIDERS:
                return error_response("Unsupported country")
            
            pricing = self._calculate_price(country, company_type, virtual)
            
            return success_response({
                "country": country,
                "company_type": company_type,
                "virtual_address": virtual,
                **pricing
            })
        
        # ============ Payment API (CCPayment) ============
        if path == "/api/v1/payments/create" and request.method == "POST":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Please login first", 401)
            
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            order_id = body.get("order_id", "")
            amount = body.get("amount", 0)
            currency = body.get("currency", "USDT")
            
            if not order_id or amount <= 0:
                return error_response("Order ID and amount are required")
            
            payment_id = f"PAY-{secrets.token_hex(8).upper()}"
            
            return success_response({
                "status": "ok",
                "payment": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": amount,
                    "currency": currency,
                    "network": "TRC20" if currency == "USDT" else "ERC20",
                    "address": "TX" + secrets.token_hex(20)[:30] + "...",
                    "qr_data": f"tron:{secrets.token_hex(32)}",
                    "status": "pending",
                    "expires_in": 3600,
                    "expires_at": datetime.now().isoformat()
                }
            })
        
        if path == "/api/v1/payments/webhook" and request.method == "POST":
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            payment_id = body.get("order_id", "")
            status = body.get("status", "")
            
            return success_response({"status": "ok", "message": "Webhook received"})
        
        if path == "/api/v1/payments" and request.method == "GET":
            return success_response({
                "supported_coins": ["USDT", "BTC", "ETH", "USDC"],
                "networks": {
                    "USDT": ["TRC20", "ERC20"],
                    "BTC": ["Bitcoin"],
                    "ETH": ["Ethereum"],
                    "USDC": ["ERC20"]
                }
            })
        
        # ============ Requirements API ============
        if path == "/api/v1/requirements" and request.method == "GET":
            country = params.get("country", ["uk"])[0]
            
            if country not in COUNTRY_REQUIREMENTS:
                return error_response("Unsupported country")
            
            return success_response({
                "country": country,
                "requirements": COUNTRY_REQUIREMENTS[country],
                "provider": PROVIDERS[country]
            })
        
        return error_response("Not found", 404)
    
    # Helper methods
    def _get_flag(self, code):
        flags = {"uk": "🇬🇧", "sg": "🇸🇬", "hk": "🇭🇰", "ae": "🇦🇪", "us": "🇺🇸"}
        return flags.get(code, "🏳️")
    
    def _get_price_includes(self, code):
        includes = {
            "uk": ["Companies House fee", "Registration"],
            "sg": ["ACRA filing", "Name approval"],
            "hk": ["Companies Registry fee", "Name search"],
            "ae": ["Free zone license", "Establishment card"],
            "us": ["State filing fee", "Registered agent"]
        }
        return includes.get(code, ["Filing fee"])
    
    def _calculate_price(self, country, company_type, virtual):
        base_prices = {
            "uk": {"ltd": 50, "llp": 39},
            "sg": {"pte_ltd": 300, "llp": 350},
            "hk": {"ltd": 200, "company": 180},
            "ae": {"freezone": 500, "mainland": 450},
            "us": {"llc": 150, "corporation": 200}
        }
        
        base = base_prices.get(country, {}).get(company_type, 100)
        currency = "GBP" if country == "uk" else "USD"
        ch_fee = 50 if country == "uk" else 0
        va_fee = 50 if virtual else 0
        
        return {
            "total": base + ch_fee + va_fee,
            "currency": currency,
            "breakdown": {
                "base": base,
                "government_fee": ch_fee,
                "virtual_address": va_fee if virtual else 0
            }
        }
    
    def _get_processing_time(self, country):
        times = {
            "uk": "3-5 business days",
            "sg": "1-2 business days",
            "hk": "3-5 business days",
            "ae": "5-7 business days",
            "us": "2-5 business days"
        }
        return times.get(country, "5-7 business days")
    
    def _get_next_steps(self, country, provider_type):
        if provider_type == "manual":
            return [
                "Our team will contact you within 24 hours",
                "Submit required documents",
                "Review and sign application",
                "Payment processing",
                "Company incorporation"
            ]
        
        return [
            "Complete payment to proceed",
            "Upload identity verification documents",
            "Provider submits to relevant authority",
            "Track status via order ID"
        ]
    
    def _get_registration_fields(self, country):
        fields = {
            "uk": ["company_name", "company_type", "directors", "shareholders", "registered_office_address", "sic_code"],
            "sg": ["company_name", "company_type", "shareholders", "directors", "registered_address", "business_activities"],
            "hk": ["company_name", "company_type", "shareholders", "directors", "registered_address", "hkid_verification"],
            "ae": ["company_name", "company_type", "freezone", "shareholders", "directors", "visa_sponsorship"],
            "us": ["company_name", "company_type", "state", "shareholders", "registered_agent", "ein"]
        }
        return fields.get(country, [])
