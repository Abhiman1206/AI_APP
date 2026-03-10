"""MCA Checker module — verifies company registration with Ministry of Corporate Affairs."""


def check_mca_status(company_name: str) -> dict:
    """Check MCA registration status of a company.

    In production, this would query MCA APIs or scrape MCA portal.
    Currently returns mock data for prototype demonstration.
    """
    return {
        "company_name": company_name,
        "cin": "U74999MH2018PTC123456",
        "registration_date": "2018-04-15",
        "status": "Active",
        "company_type": "Private Limited",
        "authorized_capital": "1,00,00,000",
        "paid_up_capital": "50,00,000",
        "directors": [
            {"name": "Rajesh Kumar", "din": "07654321", "designation": "Managing Director"},
            {"name": "Priya Sharma", "din": "08765432", "designation": "Director"},
        ],
        "annual_filings_up_to_date": True,
        "charges_registered": 1,
    }
