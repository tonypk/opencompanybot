import json
import secrets
import hashlib
from workers import WorkerEntrypoint, Response, Request


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request) -> Response:
        from urllib.parse import urlparse
        path = urlparse(request.url).path
        cors = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
        
        if request.method == "OPTIONS":
            return Response("", status=204, headers=cors)
        
        if path == "/":
            return Response(json.dumps({"name": "OpenCompanyBot API", "version": "0.1.0"}), headers=cors)
        
        if path == "/health":
            return Response(json.dumps({"status": "healthy"}), headers=cors)
        
        if path == "/api/v1/mcp/tools" and request.method == "GET":
            return Response(json.dumps({"tools": [{"name": "register_uk_company"}]}), headers=cors)
        
        if path == "/api/v1/auth/register" and request.method == "POST":
            return Response(json.dumps({"status": "ok", "token": "demo_token", "user": {"email": "demo@example.com"}}), headers=cors)
        
        if path == "/api/v1/auth/login" and request.method == "POST":
            return Response(json.dumps({"status": "ok", "token": "demo_token", "user": {"email": "demo@example.com"}}), headers=cors)
        
        if path == "/api/v1/auth/profile" and request.method == "GET":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return Response(json.dumps({"error": "Unauthorized"}), status=401, headers=cors)
            return Response(json.dumps({"user": {"email": "demo@example.com"}}), headers=cors)
        
        if path == "/api/v1/orders" and request.method == "POST":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return Response(json.dumps({"error": "Please login first", "code": "LOGIN_REQUIRED"}), status=401, headers=cors)
            
            body = {}
            try:
                body = await request.json()
            except:
                pass
            
            company_name = body.get("company_name", "Unknown")
            virtual = body.get("use_virtual_address", False)
            amount = 29 + (50 if virtual else 0)
            order_id = f"ORD-{secrets.token_hex(6).upper()}"
            
            return Response(json.dumps({
                "status": "ok",
                "order": {"id": order_id, "company_name": company_name, "amount": amount, "status": "pending"}
            }), headers=cors)
        
        if path == "/api/v1/orders" and request.method == "GET":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return Response(json.dumps({"error": "Unauthorized"}), status=401, headers=cors)
            return Response(json.dumps({"orders": []}), headers=cors)
        
        if path == "/api/v1/companies/incorporate" and request.method == "POST":
            body = {}
            try:
                body = await request.json()
            except:
                pass
            
            return Response(json.dumps({
                "status": "success",
                "company_name": body.get("company_name", ""),
                "company_number": "PENDING"
            }), headers=cors)
        
        return Response(json.dumps({"error": "Not found"}), status=404, headers=cors)
