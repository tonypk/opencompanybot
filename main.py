import json
import secrets
import hashlib
import asyncio
from workers import WorkerEntrypoint, Response, Request


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request, env) -> Response:
        from urllib.parse import urlparse
        from datetime import datetime
        
        path = urlparse(request.url).path
        query = urlparse(request.url).query
        cors = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
        
        db = getattr(self.env, "DB", None)
        
        def error_response(message, status=400):
            return Response(json.dumps({"error": message}), status=status, headers=cors)
        
        def success_response(data, status=200):
            return Response(json.dumps(data), status=status, headers=cors)
        
        if request.method == "OPTIONS":
            return Response("", status=204, headers=cors)
        
        if path == "/":
            return success_response({
                "name": "OpenCompanyBot API", 
                "version": "1.0.0",
                "countries": ["uk", "sg", "hk", "ae", "us"]
            })
        
        if path == "/health":
            return success_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
        
        # ============ Countries API ============
        if path == "/api/v1/countries" and request.method == "GET":
            return success_response({
                "countries": [
                    {
                        "code": "uk",
                        "name": "United Kingdom",
                        "flag": "🇬🇧",
                        "available": True,
                        "price": 50,
                        "ch_fee": 50,
                        "currency": "GBP"
                    },
                    {
                        "code": "sg",
                        "name": "Singapore",
                        "flag": "🇸🇬",
                        "available": False,
                        "price": 300,
                        "currency": "USD"
                    },
                    {
                        "code": "hk",
                        "name": "Hong Kong",
                        "flag": "🇭🇰",
                        "available": False,
                        "price": 200,
                        "currency": "USD"
                    },
                    {
                        "code": "ae",
                        "name": "United Arab Emirates",
                        "flag": "🇦🇪",
                        "available": False,
                        "price": 500,
                        "currency": "USD"
                    },
                    {
                        "code": "us",
                        "name": "United States",
                        "flag": "🇺🇸",
                        "available": False,
                        "price": 150,
                        "currency": "USD"
                    }
                ]
            })
        
        # ============ MCP Tools API ============
        if path == "/api/v1/mcp/tools" and request.method == "GET":
            return success_response({
                "tools": [
                    {"name": "register_uk_company", "description": "Register a UK limited company via Letsy"},
                    {"name": "check_company_status", "description": "Check company incorporation status"},
                    {"name": "search_company_name", "description": "Check if company name is available"},
                    {"name": "get_order_history", "description": "Get user's order history"}
                ]
            })
        
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
            
            if "@" not in email or "." not in email:
                return error_response("Invalid email format")
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
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
            
            company_name = body.get("company_name", "").strip()
            country = body.get("country", "uk").strip()
            virtual = body.get("use_virtual_address", False)
            company_type = body.get("company_type", "ltd")
            
            if not company_name:
                return error_response("Company name is required")
            
            # Calculate price
            if country == "uk":
                base_price = 50 if company_type == "ltd" else 39
                ch_fee = 50
                total = base_price + ch_fee + (50 if virtual else 0)
            else:
                total = 100
            
            order_id = f"ORD-{secrets.token_hex(6).upper()}"
            
            return success_response({
                "status": "ok",
                "order": {
                    "id": order_id, 
                    "company_name": company_name,
                    "country": country,
                    "company_type": company_type,
                    "virtual_address": virtual,
                    "amount": total, 
                    "currency": "GBP" if country == "uk" else "USD",
                    "status": "pending_payment",
                    "created_at": datetime.now().isoformat()
                }
            })
        
        if path == "/api/v1/orders" and request.method == "GET":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Unauthorized", 401)
            
            return success_response({
                "orders": [
                    {
                        "id": "ORD-DEMO123",
                        "company_name": "Demo Company Ltd",
                        "country": "uk",
                        "status": "completed",
                        "amount": 149,
                        "created_at": "2026-02-22T10:00:00Z"
                    }
                ]
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
            
            company_name = body.get("company_name", "").strip()
            country = body.get("country", "uk").strip()
            company_type = body.get("company_type", "ltd")
            director_name = body.get("director_name", "")
            director_dob = body.get("director_dob", "")
            director_nationality = body.get("director_nationality", "GB")
            shareholder_name = body.get("shareholder_name", director_name)
            shares = body.get("shares", "100")
            sic_code = body.get("sic_code", "62012")
            use_virtual_address = body.get("use_virtual_address", False)
            
            if not company_name:
                return error_response("Company name is required")
            
            if country != "uk":
                return error_response("Only UK is available now. Other countries coming soon.")
            
            incorporation_id = f"INC-{secrets.token_hex(8).upper()}"
            
            # Demo mode - would integrate with Letsy in production
            return success_response({
                "status": "success",
                "message": "Company incorporation submitted successfully",
                "incorporation_id": incorporation_id,
                "company_name": company_name,
                "country": country,
                "company_type": company_type,
                "company_number": "PENDING",
                "estimated_processing_time": "3-5 business days",
                "next_steps": [
                    "Complete payment to proceed",
                    "Upload identity verification documents",
                    "Letsy will submit to Companies House"
                ]
            })
        
        # ============ Company Search API ============
        if path == "/api/v1/companies/search" and request.method == "GET":
            params = dict(p.split("=") for p in query.split("&") if "=" in p)
            company_name = params.get("q", "")
            
            if not company_name:
                return error_response("Company name is required")
            
            # Demo response
            return success_response({
                "available": True,
                "company_name": company_name,
                "suggestions": []
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
            
            # Demo payment link - would integrate with CCPayment in production
            payment_id = f"PAY-{secrets.token_hex(8).upper()}"
            
            return success_response({
                "status": "ok",
                "payment": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": amount,
                    "currency": currency,
                    "network": "TRC20" if currency == "USDT" else "ERC20",
                    "address": "TXz123...456",  # Demo address
                    "status": "pending",
                    "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={payment_id}",
                    "expires_at": datetime.now().isoformat()
                }
            })
        
        if path == "/api/v1/payments/webhook" and request.method == "POST":
            # CCPayment webhook handler
            try:
                body = await request.json()
            except:
                return error_response("Invalid JSON")
            
            payment_id = body.get("order_id", "")
            status = body.get("status", "")
            
            # Process payment status
            if status == "confirmed":
                # Update order status
                return success_response({"status": "ok", "message": "Payment confirmed"})
            
            return success_response({"status": "received"})
        
        if path == "/api/v1/payments" and request.method == "GET":
            auth = request.headers.get("Authorization", "")
            if "Bearer" not in auth:
                return error_response("Unauthorized", 401)
            
            return success_response({
                "payments": [],
                "supported_coins": ["USDT", "BTC", "ETH"],
                "networks": {
                    "USDT": ["TRC20", "ERC20"],
                    "BTC": ["Bitcoin"],
                    "ETH": ["Ethereum"]
                }
            })
        
        return error_response("Not found", 404)
