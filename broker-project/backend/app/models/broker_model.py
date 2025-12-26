"""
Broker Model
============
Data models and schemas for broker entities.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BrokerBasicInfo:
    """Basic broker information."""
    member_name: str
    member_code: str
    sebi_reg_no: str
    sr_no: Optional[int] = None


@dataclass
class BrokerContact:
    """Broker contact information."""
    address: Optional[str] = None
    city: Optional[str] = None
    pin_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


@dataclass
class BrokerManagement:
    """Broker management details."""
    ceo_name: Optional[str] = None
    compliance_officer: Optional[str] = None
    directors: List[str] = field(default_factory=list)


@dataclass
class BrokerAnalytics:
    """Broker performance analytics."""
    active_clients: int = 0
    total_clients: int = 0
    client_bank_accounts: int = 0
    complaints: int = 0


@dataclass
class BrokerComplete:
    """Complete broker information."""
    basic_info: BrokerBasicInfo
    contact: BrokerContact
    management: BrokerManagement
    analytics: BrokerAnalytics
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_mongodb_doc(cls, doc: Dict[str, Any]) -> 'BrokerComplete':
        """
        Create BrokerComplete instance from MongoDB document.
        
        Args:
            doc: MongoDB document
            
        Returns:
            BrokerComplete instance
        """
        # Extract basic info
        basic_info = BrokerBasicInfo(
            member_name=doc.get("Member Name", ""),
            member_code=doc.get("Member Code", ""),
            sebi_reg_no=doc.get("SEBI Registration no", ""),
            sr_no=doc.get("_metadata", {}).get("sr_no")
        )
        
        # Extract contact info
        registered_office = doc.get("Registered_Office", {})
        website_app = doc.get("website_app", {})
        contact = BrokerContact(
            address=registered_office.get("Registered Office Address"),
            city=registered_office.get("City"),
            pin_code=registered_office.get("Pin Code"),
            phone=registered_office.get("Phone Number"),
            email=registered_office.get("Email ID"),
            website=website_app.get("Website Address")
        )
        
        # Extract management info
        key_mgmt = doc.get("key_management_details", {})
        ceo_name = None
        compliance_officer = None
        
        if isinstance(key_mgmt, dict):
            md_ceo = key_mgmt.get("Managing_Director_CEO", {})
            if isinstance(md_ceo, dict):
                ceo_name = md_ceo.get("Name")
            
            comp_officer = key_mgmt.get("Compliance_Officer", {})
            if isinstance(comp_officer, dict):
                compliance_officer = comp_officer.get("Name")
        
        management = BrokerManagement(
            ceo_name=ceo_name,
            compliance_officer=compliance_officer
        )
        
        # Extract analytics
        active_clients = 0
        summary_info = doc.get("summary_trading_member_info", {})
        data_by_period = summary_info.get("Data_By_Period", {})
        if data_by_period:
            periods = list(data_by_period.keys())
            if periods:
                latest_period = periods[-1]
                period_data = data_by_period[latest_period]
                if isinstance(period_data, dict):
                    try:
                        active_clients = int(
                            period_data.get("Total_number_of_active_clients", 0)
                        )
                    except (ValueError, TypeError):
                        active_clients = 0
        
        analytics = BrokerAnalytics(active_clients=active_clients)
        
        return cls(
            basic_info=basic_info,
            contact=contact,
            management=management,
            analytics=analytics,
            raw_data=doc
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "basic_info": {
                "member_name": self.basic_info.member_name,
                "member_code": self.basic_info.member_code,
                "sebi_reg_no": self.basic_info.sebi_reg_no,
                "sr_no": self.basic_info.sr_no
            },
            "contact": {
                "address": self.contact.address,
                "city": self.contact.city,
                "pin_code": self.contact.pin_code,
                "phone": self.contact.phone,
                "email": self.contact.email,
                "website": self.contact.website
            },
            "management": {
                "ceo_name": self.management.ceo_name,
                "compliance_officer": self.management.compliance_officer,
                "directors": self.management.directors
            },
            "analytics": {
                "active_clients": self.analytics.active_clients,
                "total_clients": self.analytics.total_clients,
                "client_bank_accounts": self.analytics.client_bank_accounts,
                "complaints": self.analytics.complaints
            }
        }
