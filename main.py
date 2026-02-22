import json
import secrets
import hashlib
from workers import WorkerEntrypoint, Response, Request


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request, env) -> Response:
        from urllib.parse import urlparse
        from datetime import datetime
        
        path = urlparse(request.url).path
        cors = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
        
        db = getattr(self.env, "DB", None)
        
        def error_response(message, status=400):
            return Response(json.dumps({"error": message}), status=status, headers=cors)
        
        def success_response(data, status=200):
            return Response(json.dumps(data), status=status, headers=cors)
        
        if request.method == "OPTIONS":
            return Response("", status=204, headers=cors)
        
        if path == "/":
            return success_response({"name": "OpenCompanyBot API", "version": "0.2.0"})
        
        if path == "/health":
            return success_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
        
        if path == "/api/v1/mcp/tools" and request.method == "GET":
            return success_response({
                "tools": [
                    {"name": "register_uk_company", "description": "Register a UK limited company"},
                    {"name": "check_company_status", "description": "Check company incorporation status"},
                    {"name": "get_order_history", "description": "Get user's order history"}
                ]
            })
        
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
            
            if "@" not in email or "." not in email:
                return error_response("Invalid email format")
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            token = secrets.token_hex(32)
            created_at = datetime.now().isoformat()
            
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
        
        if path == "/api/v1/orders" and request.method == "POST":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Please login first", 401)
            
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            company_name = body.get("company_name", "").strip()
            if not company_name:
                return error_response("Company name is required")
            
            virtual = body.get("use_virtual_address", False)
            company_type = body.get("company_type", "ltd")
            
            if company_type == "llp":
                amount = 39 + (50 if virtual else 0)
            else:
                amount = 29 + (50 if virtual else 0)
            
            order_id = f"ORD-{secrets.token_hex(6).upper()}"
            created_at = datetime.now().isoformat()
            
            return success_response({
                "status": "ok",
                "order": {
                    "id": order_id, 
                    "company_name": company_name,
                    "company_type": company_type,
                    "virtual_address": virtual,
                    "amount": amount, 
                    "currency": "GBP",
                    "status": "pending",
                    "created_at": created_at
                }
            })
        
        if path == "/api/v1/orders" and request.method == "GET":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Unauthorized", 401)
            
            return success_response({
                "orders": [],
                "message": "No orders yet"
            })
        
        if path == "/api/v1/companies/incorporate" and request.method == "POST":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Please login first", 401)
            
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            company_name = body.get("company_name", "").strip()
            if not company_name:
                return error_response("Company name is required")
            
            company_type = body.get("company_type", "ltd")
            directors = body.get("directors", [])
            shareholders = body.get("shareholders", [])
            sic_codes = body.get("sic_codes", [])
            registered_office_address = body.get("registered_office_address", {})
            
            incorporation_id = f"INC-{secrets.token_hex(8).upper()}"
            
            return success_response({
                "status": "success",
                "message": "Company incorporation submitted successfully",
                "incorporation_id": incorporation_id,
                "company_name": company_name,
                "company_type": company_type,
                "company_number": "PENDING",
                "estimated_processing_time": "3-5 business days"
            })
        
        if path == "/api/v1/companies/search" and request.method == "GET":
            company_name = request.url.split("?q=")[1] if "?q=" in request.url else ""
            
            return success_response({
                "companies": [],
                "message": "Company search requires API key"
            })
        
        return error_response("Not found", 404)
