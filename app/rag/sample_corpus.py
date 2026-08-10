"""
Deterministic Sample Enterprise Document Corpus
Contains sample contracts, SLAs, post-mortems, and policies for local testing and ingestion validation.
"""

from typing import List, Dict, Any

SAMPLE_ENTERPRISE_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "filename": "carrier_logistics_x_sla_contract_2025.md",
        "category": "contracts",
        "doc_id": "DOC-CONTRACT-CARRIER-X",
        "effective_date": "2025-01-01",
        "content": (
            "# CARRIER LOGISTICS PARTNER X - MASTER SERVICES AGREEMENT\n"
            "Effective Date: 2025-01-01 | Version: 2.1\n\n"
            "## SECTION 1. SCOPE OF SERVICES\n"
            "Carrier Logistics Partner X agrees to provide regional freight and last-mile package delivery "
            "services across Midwest and East Coast logistics zones.\n\n"
            "## SECTION 4.2 - SLA PENALTIES AND BREACH THRESHOLDS\n"
            "Carrier Logistics Partner X agrees to maintain a minimum On-Time Delivery SLA rate of 95.0%. "
            "If the monthly SLA breach rate exceeds 5.0% (defined as delivery delays greater than 48 hours), "
            "Customer is entitled to a liquidated penalty of $50.00 USD per delayed shipment.\n\n"
            "## SECTION 9. TERMINATION CLAUSE\n"
            "Either party may terminate this agreement upon 60 days written notice if delivery SLA breaches "
            "exceed the threshold for two consecutive operational quarters."
        ),
    },
    {
        "filename": "midwest_warehouse_q3_postmortem.md",
        "category": "post_mortems",
        "doc_id": "DOC-POSTMORTEM-MIDWEST-Q3",
        "effective_date": "2025-10-05",
        "content": (
            "# MIDWEST HUB OPERATIONAL POST-MORTEM REPORT - Q3\n"
            "Date: 2025-10-05 | Author: Logistics Incident Response Team\n\n"
            "## EXECUTIVE SUMMARY\n"
            "Gross margin erosion in the Midwest hub reached $30,000 USD during Q3.\n\n"
            "## ROOT-CAUSE ANALYSIS & FINANCIAL BREAKDOWN\n"
            "Investigation identified two primary operational cost drivers:\n"
            "1. Regional 3PL fuel surcharges due to peak-season carrier rate amendments ($18,200 USD impact, 60.7%).\n"
            "2. Damaged return scrap write-offs caused by faulty packaging equipment at sorting station 4 ($11,800 USD impact, 39.3%).\n\n"
            "## CORRECTIVE ACTION PLAN\n"
            "Sorting station 4 packaging units recalibrated on October 2, 2025."
        ),
    },
    {
        "filename": "3pl_peak_season_fuel_surcharge_amendment.md",
        "category": "contracts",
        "doc_id": "DOC-AMENDMENT-FUEL-SURCHARGE",
        "effective_date": "2025-08-15",
        "content": (
            "# AMENDMENT NO. 2 TO LOGISTICS FREIGHT AGREEMENT\n"
            "Effective Date: 2025-08-15 | Category: Shipping Surcharges\n\n"
            "## REGIONAL FUEL SURCHARGE NOTICE\n"
            "Effective August 15, 2025, a regional shipping surcharge of 28% applies to all Midwest hub "
            "freight routes under 3PL logistics partner agreements due to diesel index variations."
        ),
    },
    {
        "filename": "supplier_agreement_alpha_corp.md",
        "category": "contracts",
        "doc_id": "DOC-SUPPLIER-ALPHA-CORP",
        "effective_date": "2025-03-01",
        "content": (
            "# ALPHA CORP SUPPLIER MASTER AGREEMENT\n"
            "Effective Date: 2025-03-01 | Lead Time: 14 Days\n\n"
            "## SECTION 3. SUPPLY GUARANTEES\n"
            "Alpha Corp guarantees a component defect rate under 0.2% and agrees to full replacement costs "
            "for any defective manufacturing batches."
        ),
    },
    {
        "filename": "customer_refund_policy_2025.md",
        "category": "policies",
        "doc_id": "DOC-POLICY-REFUNDS-2025",
        "effective_date": "2025-01-15",
        "content": (
            "# CUSTOMER REFUND AND RETURN POLICY 2025\n"
            "Effective Date: 2025-01-15 | Version: 1.0\n\n"
            "## SECTION 2. LATE DELIVERY REFUNDS\n"
            "Customers experiencing carrier delays exceeding 48 hours are eligible for a 100% shipping fee "
            "refund upon request."
        ),
    },
]
