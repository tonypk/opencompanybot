"""
Hong Kong Companies Registry TPSI Integration
Reference: https://www.cr.gov.hk

TPSI (Trade Principal and Supporting Information) API Integration
for Hong Kong Company Registration

Note: This is a simulation module. Actual integration requires:
1. Registration with Companies Registry e-filing service
2. Digital certificate acquisition
3. API credentials from CR
"""

import hashlib
import secrets
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Optional


class HongKongTPSI:
    """
    Hong Kong Companies Registry TPSI Integration
    For company incorporation and other filing services
    """
    
    # Production and Test endpoints
    PRODUCTION_URL = "https://www.cr.gov.hk/efiling/service"
    TEST_URL = "https://www.cr.gov.hk/efiling/test/service"
    
    def __init__(self, crn: str = None, digital_cert_path: str = None, test_mode: bool = True):
        """
        Initialize TPSI connection
        
        Args:
            crn: Companies Registry Number (CRN) for the filing agent
            digital_cert_path: Path to digital certificate for authentication
            test_mode: Use test environment
        """
        self.crn = crn or "DEMO_AGENT_CRN"
        self.cert_path = digital_cert_path
        self.test_mode = test_mode
        self.endpoint = self.TEST_URL if test_mode else self.PRODUCTION_URL
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random = secrets.token_hex(4).upper()
        return f"HKCR-{timestamp}-{random}"
    
    def _generate_hashing(self, data: str) -> str:
        """Generate SHA-256 hash for data integrity"""
        return hashlib.sha256(data.encode()).hexdigest().upper()
    
    def search_company_name(self, company_name: str) -> Dict:
        """
        Check company name availability
        
        Args:
            company_name: Company name to check
            
        Returns:
            Dictionary with availability status
        """
        transaction_id = self._generate_transaction_id()
        
        # Simulate response (actual API would check against CR database)
        name_upper = company_name.upper()
        
        # Reserved words that require special approval
        reserved_words = ['BANK', 'INSURANCE', 'TRUST', 'CHAMBER', 'UNIVERSITY', 'INSTITUTE']
        requires_approval = any(word in name_upper for word in reserved_words)
        
        # Simulate some names as taken
        taken_names = ['OPENCOMPANY BOT LIMITED', 'TEST COMPANY LIMITED']
        
        if name_upper in taken_names:
            return {
                "available": False,
                "transaction_id": transaction_id,
                "message": "Company name is not available",
                "similar_names": ["OpenCompany Limited", "Test Corp Limited"]
            }
        
        return {
            "available": not requires_approval,
            "transaction_id": transaction_id,
            "message": "Company name available" if not requires_approval else "Company name requires special approval",
            "requires_approval": requires_approval,
            "next_steps": [
                "Submit incorporation application",
                "Pay incorporation fee",
                "Provide director/shareholder details"
            ]
        }
    
    def incorporate_company(self, company_data: Dict) -> Dict:
        """
        Submit company incorporation application
        
        Args:
            company_data: Dictionary containing:
                - company_name: Company name
                - company_type: "limited" or "unlimited"
                - directors: List of director info
                - shareholders: List of shareholder info
                - registered_address: Hong Kong registered address
                - secretary: Company secretary info (if required)
                
        Returns:
            Dictionary with incorporation result
        """
        transaction_id = self._generate_transaction_id()
        
        # Validate required fields
        required_fields = ['company_name', 'directors', 'shareholders', 'registered_address']
        for field in required_fields:
            if field not in company_data:
                return {
                    "status": "error",
                    "message": f"Missing required field: {field}",
                    "transaction_id": transaction_id
                }
        
        # Generate company number (format: XXXXXXXX)
        company_number = str(int(datetime.now().timestamp()))[-8:]
        
        # Generate BRN (Business Registration Number) format: XX-XXXXXXX
        brn_year = datetime.now().strftime("%y")
        brn_number = secrets.token_hex(3).upper()
        brn = f"{brn_year}-{brn_number}"
        
        # Build incorporation XML message
        xml_message = self._build_incorporation_xml(company_data, transaction_id)
        
        # Simulate successful submission
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "company_number": company_number,
            "brn": brn,
            "company_name": company_data.get("company_name"),
            "company_type": company_data.get("company_type", "limited"),
            "incorporation_date": datetime.now().strftime("%Y-%m-%d"),
            "message": "Company incorporation submitted successfully",
            "xml_generated": len(xml_message) > 0,
            "estimated_processing_time": "1-2 business days",
            "next_steps": [
                "Pay incorporation fee (HK$1720)",
                "Collect certificate of incorporation",
                "Apply for Business Registration Certificate",
                "Open bank account"
            ],
            "fees": {
                "incorporation_fee": 1720,
                "business_registration": 2500,
                "total": 4220,
                "currency": "HKD"
            }
        }
    
    def _build_incorporation_xml(self, company_data: Dict, transaction_id: str) -> str:
        """Build TPSI incorporation XML message"""
        
        root = ET.Element("IncorporationRequest")
        root.set("xmlns", "http://www.cr.gov.hk/tpsi/2024")
        
        # Header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "TransactionID").text = transaction_id
        ET.SubElement(header, "CRN").text = self.crn
        ET.SubElement(header, "SubmissionDate").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Company Details
        company = ET.SubElement(root, "Company")
        ET.SubElement(company, "CompanyName").text = company_data.get("company_name", "")
        ET.SubElement(company, "CompanyType").text = company_data.get("company_type", "limited")
        ET.SubElement(company, "CompanyNumber").text = ""  # Assigned by CR
        
        # Registered Address
        addr = company_data.get("registered_address", {})
        address = ET.SubElement(company, "RegisteredAddress")
        ET.SubElement(address, "Room").text = addr.get("room", "")
        ET.SubElement(address, "Floor").text = addr.get("floor", "")
        ET.SubElement(address, "Block").text = addr.get("block", "")
        ET.SubElement(address, "Building").text = addr.get("building", "")
        ET.SubElement(address, "Street").text = addr.get("street", "")
        ET.SubElement(address, "District").text = addr.get("district", "")
        
        # Directors
        directors = ET.SubElement(company, "Directors")
        for director in company_data.get("directors", []):
            dir_elem = ET.SubElement(directors, "Director")
            ET.SubElement(dir_elem, "Type").text = director.get("type", "individual")
            ET.SubElement(dir_elem, "Name").text = director.get("name", "")
            ET.SubElement(dir_elem, "HKID").text = director.get("hkid", "")  # Hong Kong ID or passport
            ET.SubElement(dir_elem, "Nationality").text = director.get("nationality", "")
            ET.SubElement(dir_elem, "Address").text = director.get("address", "")
        
        # Shareholders
        shareholders = ET.SubElement(company, "Shareholders")
        for shareholder in company_data.get("shareholders", []):
            sh_elem = ET.SubElement(shareholders, "Shareholder")
            ET.SubElement(sh_elem, "Name").text = shareholder.get("name", "")
            ET.SubElement(sh_elem, "Shares").text = str(shareholder.get("shares", 1))
            ET.SubElement(sh_elem, "Type").text = shareholder.get("type", "individual")
        
        # Company Secretary (required for Hong Kong companies)
        if company_data.get("secretary"):
            sec = company_data.get("secretary", {})
            secretary = ET.SubElement(company, "Secretary")
            ET.SubElement(secretary, "Name").text = sec.get("name", "")
            ET.SubElement(secretary, "Address").text = sec.get("address", "")
        
        return ET.tostring(root, encoding='unicode')
    
    def get_company_details(self, company_number: str) -> Dict:
        """
        Get company details from CR
        
        Args:
            company_number: Hong Kong company number
            
        Returns:
            Dictionary with company details
        """
        transaction_id = self._generate_transaction_id()
        
        # Simulate company details (actual API would fetch from CR)
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "company_number": company_number,
            "company_name": "EXAMPLE COMPANY LIMITED",
            "company_type": "private limited",
            "incorporation_date": "2024-01-15",
            "status": "live",
            "registered_address": {
                "room": "",
                "floor": "10",
                "block": "A",
                "building": "Tech Centre",
                "street": "123 Queen's Road Central",
                "district": "Central and Western",
                "city": "Hong Kong"
            },
            "directors": [
                {"name": "John Smith", "nationality": "British"}
            ],
            "shareholders": [
                {"name": "John Smith", "shares": 100}
            ],
            "secretary": {"name": "HK Corporate Services Ltd"},
            "annual_return": {
                "next_due": "2025-01-15",
                "last_filed": "2024-01-15"
            }
        }
    
    def file_annual_return(self, company_number: str, data: Dict) -> Dict:
        """
        File annual return
        
        Args:
            company_number: Company registration number
            data: Annual return data
            
        Returns:
            Filing result
        """
        transaction_id = self._generate_transaction_id()
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "company_number": company_number,
            "filing_date": datetime.now().strftime("%Y-%m-%d"),
            "acknowledgment_number": f"AR-{transaction_id}",
            "fee_paid": 105,
            "currency": "HKD",
            "next_due": f"{datetime.now().year + 1}-01-15"
        }
    
    def check_name_availability_batch(self, names: list) -> Dict:
        """
        Batch check name availability
        
        Args:
            names: List of company names to check
            
        Returns:
            Dictionary with availability for each name
        """
        results = {}
        for name in names:
            result = self.search_company_name(name)
            results[name] = {
                "available": result["available"],
                "message": result["message"]
            }
        
        return {
            "transaction_id": self._generate_transaction_id(),
            "results": results,
            "total_checked": len(names)
        }


# Integration helper functions
def format_hk_address(address_parts: Dict) -> str:
    """Format Hong Kong address for submission"""
    parts = []
    for key in ['room', 'floor', 'block', 'building', 'street']:
        if address_parts.get(key):
            parts.append(address_parts[key])
    if address_parts.get('district'):
        parts.append(address_parts['district'])
    parts.append("Hong Kong")
    return ", ".join(filter(None, parts))


def validate_hkid(hkid: str) -> bool:
    """
    Validate Hong Kong ID format
    Format: XXXXXXXX(A)
    """
    if len(hkid) < 8:
        return False
    # Basic validation - actual validation is more complex
    return True


# Example usage
if __name__ == "__main__":
    # Initialize TPSI client
    hk_tpsi = HongKongTPSI(test_mode=True)
    
    # Check company name
    print("=== Checking company name ===")
    result = hk_tpsi.search_company_name("Tech Solutions Limited")
    print(result)
    
    # Incorporate company
    print("\n=== Incorporating company ===")
    company_data = {
        "company_name": "Tech Solutions Limited",
        "company_type": "limited",
        "registered_address": {
            "room": "10",
            "floor": "15",
            "block": "A",
            "building": "Cyberport Centre",
            "street": "100 Cyberport Road",
            "district": "Southern District"
        },
        "directors": [
            {
                "name": "Chan Tai Man",
                "hkid": "A123456(7)",
                "nationality": "Hong Kong",
                "address": "Flat 1, 10 Tower 1, Happy Garden, Hong Kong"
            }
        ],
        "shareholders": [
            {
                "name": "Chan Tai Man",
                "shares": 100,
                "type": "individual"
            }
        ],
        "secretary": {
            "name": "HK Corporate Services Limited",
            "address": "Room 1001, 10 Queen's Road Central, Hong Kong"
        }
    }
    
    result = hk_tpsi.incorporate_company(company_data)
    print(result)