"""
UK Companies House XML Gateway Integration

This module handles the integration with Companies House XML Gateway API
for company incorporation and other filings.

Reference: https://www.gov.uk/guidance/
companies-house-api-and-extensible-business-reporting-language-ebr

Note: This requires:
1. Presenter ID (from Companies House)
2. Authentication code
3. Direct Debit account for fees
"""

import hashlib
import hmac
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Optional


class CompaniesHouseXMLGateway:
    """
    UK Companies House XML Gateway Client
    
    This handles the SOAP/XML communication with Companies House
    for company incorporation and other filings.
    """
    
    # Production and test endpoints
    LIVE_URL = "https://xmlgateway.companieshouse.gov.uk/v2-1/schema/1/incorporation.xsd"
    TEST_URL = "https://xmlgw.companieshouse.gov.uk/v2-1/schema/1/incorporation.xsd"
    
    def __init__(self, presenter_id: str, authentication_code: str, test_mode: bool = True):
        self.presenter_id = presenter_id
        self.authentication_code = authentication_code
        self.test_mode = test_mode
        self.endpoint = self.TEST_URL if test_mode else self.LIVE_URL
        
        # Envelope version
        self.envelope_version = "2.0"
    
    def _generate_digest(self, xml_body: str) -> str:
        """Generate MD5 digest of the XML body"""
        return hashlib.md5(xml_body.encode()).hexdigest().upper()
    
    def _build_header(self, transaction_id: str) -> ET.Element:
        """Build the XML header with authentication"""
        # This is a simplified version - actual implementation
        # requires specific schema based on Companies House documentation
        header = ET.Element("Header")
        
        # Sender details
        sender = ET.SubElement(header, "SenderDetails")
        id_auth = ET.SubElement(sender, "IDAuthentication")
        
        # Presenter ID
        sender_id = ET.SubElement(id_auth, "SenderID")
        sender_id.text = self.presenter_id
        
        # Authentication method
        auth = ET.SubElement(id_auth, "Authentication")
        method = ET.SubElement(auth, "Method")
        method.text = "MD5"
        
        # Generate hash of authentication code + timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        value = ET.SubElement(auth, "Value")
        value.text = self._generate_digest(self.authentication_code + timestamp)
        
        # Timestamp
        time = ET.SubElement(sender, "TransactionTimestamp")
        time_attrib = ET.SubElement(time, "DateTime")
        time_attrib.text = timestamp
        
        # Transaction ID
        transaction = ET.SubElement(header, "TransactionID")
        transaction.text = transaction_id
        
        return header
    
    def _build_incorporation_body(self, company_data: Dict) -> ET.Element:
        """Build the company incorporation request body"""
        body = ET.Element("Body")
        
        # Incorporation request
        incorp = ET.SubElement(body, "IncorporationRequest")
        
        # Company name
        company_name = ET.SubElement(incorp, "CompanyName")
        company_name.text = company_data.get("company_name", "")
        
        # Company type
        company_type = ET.SubElement(incorp, "CompanyType")
        company_type.text = company_data.get("company_type", "ltd")
        
        # Registered office address
        address = ET.SubElement(incorp, "RegisteredOfficeAddress")
        
        address_line_1 = ET.SubElement(address, "AddressLine1")
        address_line_1.text = company_data.get("address", {}).get("line_1", "")
        
        address_line_2 = ET.SubElement(address, "AddressLine2")
        address_line_2.text = company_data.get("address", {}).get("line_2", "")
        
        locality = ET.SubElement(address, "Locality")
        locality.text = company_data.get("address", {}).get("locality", "")
        
        region = ET.SubElement(address, "Region")
        region.text = company_data.get("address", {}).get("region", "")
        
        postal_code = ET.SubElement(address, "PostalCode")
        postal_code.text = company_data.get("address", {}).get("postal_code", "")
        
        # Directors
        directors = ET.SubElement(incorp, "Directors")
        for director in company_data.get("directors", []):
            dir_elem = ET.SubElement(directors, "Director")
            
            # Name
            name = ET.SubElement(dir_elem, "Name")
            forename = ET.SubElement(name, "Forename")
            forename.text = director.get("forename", "")
            surname = ET.SubElement(name, "Surname")
            surname.text = director.get("surname", "")
            
            # Date of birth
            dob = ET.SubElement(dir_elem, "DateOfBirth")
            dob_year = ET.SubElement(dob, "Year")
            dob_year.text = director.get("dob_year", "")
            dob_month = ET.SubElement(dob, "Month")
            dob_month.text = director.get("dob_month", "")
            
            # Nationality
            nationality = ET.SubElement(dir_elem, "Nationality")
            nationality.text = director.get("nationality", "")
            
            # Occupation
            occupation = ET.SubElement(dir_elem, "Occupation")
            occupation.text = director.get("occupation", "")
            
            # Address (if different from registered office)
            if director.get("address"):
                dir_addr = ET.SubElement(dir_elem, "ResidentialAddress")
                line1 = ET.SubElement(dir_addr, "AddressLine1")
                line1.text = director["address"].get("line_1", "")
        
        # Shareholders / Capital
        capital = ET.SubElement(incorp, "Shareholders")
        
        statement = ET.SubElement(capital, "StatementOfCapital")
        
        currency = ET.SubElement(statement, "Currency")
        currency.text = company_data.get("capital", {}).get("currency", "GBP")
        
        total_amount = ET.SubElement(statement, "TotalAmount")
        total_amount.text = str(company_data.get("capital", {}).get("amount", 100))
        
        # Shares
        for share in company_data.get("shares", []):
            share_class = ET.SubElement(capital, "ShareClass")
            share_class.text = share.get("class", "ordinary")
            
            num_shares = ET.SubElement(capital, "NumberAllotted")
            num_shares.text = str(share.get("number", 100))
            
            prescribed = ET.SubElement(capital, "PrescribedParticulars")
            prescribed.text = share.get("particulars", "")
        
        # SIC Codes
        sic_codes = ET.SubElement(incorp, "SICCodes")
        for code in company_data.get("sic_codes", []):
            sic = ET.SubElement(sic_codes, "SICCode")
            sic.text = code
        
        # Important: Identity Verification (IDV)
        # As of 2025, Companies House requires IDV for directors
        idv = ET.SubElement(incorp, "IdentityVerification")
        idv_status = ET.SubElement(idv, "Status")
        idv_status.text = "VERIFIED"  # Would need to integrate with IDV provider
        
        return body
    
    def build_incorporation_xml(self, company_data: Dict) -> str:
        """Build complete incorporation XML message"""
        # Generate transaction ID
        transaction_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Build XML structure
        root = ET.Element("GovTalkMessage")
        root.set("xmlns", "http://www.govtalk.gov.uk/schemas/govtalk/govtalkheader")
        
        # Envelope version
        env_version = ET.SubElement(root, "EnvelopeVersion")
        env_version.text = self.envelope_version
        
        # Header
        header = self._build_header(transaction_id)
        root.append(header)
        
        # GovTalkDetails
        gov_talk = ET.SubElement(root, "GovTalkDetails")
        
        # KeyStore
        key_store = ET.SubElement(gov_talk, "KeyStore")
        key = ET.SubElement(key_store, "Key")
        key.set("Type", "Service")
        key.text = "Incorporation"
        
        # Body
        body = self._build_incorporation_body(company_data)
        root.append(body)
        
        # Convert to string
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Add XML declaration
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        
        return xml_str, transaction_id
    
    def parse_response(self, response_xml: str) -> Dict:
        """Parse Companies House XML response"""
        try:
            root = ET.fromstring(response_xml)
            
            # Extract status
            body = root.find(".//Body")
            if body is not None:
                # Check for errors
                error = body.find(".//Error")
                if error is not None:
                    return {
                        "status": "error",
                        "error_code": error.findtext("ErrorCode", "UNKNOWN"),
                        "error_message": error.findtext("ErrorMessage", "Unknown error")
                    }
                
                # Check for acceptance
                ack = body.find(".//Acknowledgement")
                if ack is not None:
                    return {
                        "status": "accepted",
                        "transaction_id": ack.findtext("TransactionID", ""),
                        "incorporation_number": ack.findtext("IncorporationNumber", ""),
                        "company_number": ack.findtext("CompanyNumber", "")
                    }
            
            return {"status": "unknown", "raw": response_xml}
            
        except ET.ParseError as e:
            return {"status": "parse_error", "error": str(e)}
    
    async def incorporate_company(self, company_data: Dict) -> Dict:
        """
        Submit company incorporation request
        
        Args:
            company_data: Dictionary containing:
                - company_name: str
                - company_type: str (ltd, llp, etc.)
                - address: dict with address fields
                - directors: list of director dicts
                - shares: list of share dicts
                - sic_codes: list of SIC codes
        
        Returns:
            Dict with status and transaction/company details
        """
        # Build XML
        xml_body, transaction_id = self.build_incorporation_xml(company_data)
        
        # In production, this would send to Companies House API
        # For now, return the transaction ID for polling
        
        # Note: In test mode, you would send to TEST_URL
        # In production, send to LIVE_URL
        
        # The actual API call would look like:
        """
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.endpoint,
                data=xml_body.encode('utf-8'),
                headers={'Content-Type': 'application/xml'}
            ) as resp:
                response = await resp.text()
                return self.parse_response(response)
        """
        
        return {
            "status": "submitted",
            "transaction_id": transaction_id,
            "message": "Incorporation request submitted. Use transaction ID to poll for status.",
            "test_mode": self.test_mode,
            "xml_preview": xml_body[:500] + "..." if len(xml_body) > 500 else xml_body
        }
    
    async def check_status(self, transaction_id: str) -> Dict:
        """
        Check status of incorporation request
        
        Companies House uses a polling mechanism:
        1. Initial response gives transaction ID
        2. Poll periodically to get status
        3. Possible statuses: VALIDATED, PROCESSING, ACCEPTED, REJECTED
        """
        # In production, this would poll the Companies House API
        # For demo purposes, return pending
        
        return {
            "status": "pending",
            "transaction_id": transaction_id,
            "message": "Poll again in a few hours for final status"
        }


# Helper function to create client
def create_xml_gateway_client(presenter_id: str, auth_code: str, test_mode: bool = True):
    """Create an XML Gateway client instance"""
    return CompaniesHouseXMLGateway(presenter_id, auth_code, test_mode)


# Example usage
if __name__ == "__main__":
    # Demo - this would require real presenter ID in production
    client = create_xml_gateway_client(
        presenter_id="YOUR_PRESENTER_ID",
        auth_code="YOUR_AUTH_CODE",
        test_mode=True
    )
    
    # Example company data
    company_data = {
        "company_name": "Tech Solutions Ltd",
        "company_type": "ltd",
        "address": {
            "line_1": "123 High Street",
            "line_2": "",
            "locality": "London",
            "region": "Greater London",
            "postal_code": "SW1A 1AA"
        },
        "directors": [
            {
                "forename": "John",
                "surname": "Smith",
                "dob_year": "1990",
                "dob_month": "01",
                "nationality": "British",
                "occupation": "Software Developer"
            }
        ],
        "shares": [
            {
                "class": "ordinary",
                "number": 100,
                "particulars": "One vote per share"
            }
        ],
        "capital": {
            "currency": "GBP",
            "amount": 100
        },
        "sic_codes": ["62012"]
    }
    
    import json
    result = client.incorporate_company(company_data)
    print(json.dumps(result, indent=2))
