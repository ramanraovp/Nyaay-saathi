import json
import os

# I am Defineng legal codes and sections for reference..Its useful to know about my legal knowledge and app's legal knowlege on the same

LEGAL_CODES = {
    "IPC": "Indian Penal Code",
    "CrPC": "Code of Criminal Procedure",
    "CPC": "Code of Civil Procedure",
    "IT Act": "Information Technology Act",
    "RTI Act": "Right to Information Act",
    "POCSO": "Protection of Children from Sexual Offences Act",
    "RERA": "Real Estate (Regulation and Development) Act",
    "SARFAESI": "Securitisation and Reconstruction of Financial Assets and Enforcement of Securities Interest Act"
}

# Common IPC sections
IPC_SECTIONS = {
    "Section 299-304": "Culpable homicide and murder",
    "Section 304A": "Death by negligence",
    "Section 319-338": "Causing hurt and grievous hurt",
    "Section 339-348": "Wrongful restraint and confinement",
    "Section 375-376E": "Sexual offenses",
    "Section 378-382": "Theft",
    "Section 383-389": "Extortion",
    "Section 390-402": "Robbery and dacoity",
    "Section 403-404": "Criminal misappropriation of property",
    "Section 405-409": "Criminal breach of trust",
    "Section 415-420": "Cheating",
    "Section 441-462": "Criminal trespass",
    "Section 463-477A": "Forgery and counterfeiting",
    "Section 498A": "Matrimonial cruelty",
    "Section 499-502": "Defamation"
}

# Loading myyyyy legal knowledge base
try:
    with open('legal_knowledge_base.json', 'r') as f:
        legal_db = json.load(f)
except FileNotFoundError:
    legal_db = {
        "legal_qa_pairs": [
            {
                "question": "What are my rights during an arrest?",
                "answer": "During an arrest in India, you have several rights under Section 41 and 50 of the CrPC and Article 22 of the Constitution:\n\n1. Right to know the grounds of arrest\n2. Right to inform a relative or friend about your arrest\n3. Right to legal representation/meet a lawyer of your choice\n4. Right to be produced before a magistrate within 24 hours\n5. Right to medical examination\n6. Right against self-incrimination (you can remain silent)\n7. Right against torture or illegal detention\n\nWomen cannot be arrested after sunset and before sunrise except in exceptional circumstances, and only by female police officers.\n\nI am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters."
            },
            {
                "question": "How do I file an FIR?",
                "answer": "To file a First Information Report (FIR) in India:\n\n1. Visit the police station having jurisdiction where the crime occurred\n2. Provide details of the incident to the officer in charge (date, time, place, description of the event, names of suspects if known)\n3. The police officer must register your FIR for cognizable offenses (under Section 154 of CrPC)\n4. Review the FIR before signing it\n5. Collect a free copy of the FIR\n\nIf the police refuse to register your FIR:\n- Approach the Superintendent of Police or other higher officers\n- File a complaint to the Judicial Magistrate under Section 156(3) CrPC\n- File a complaint online on the state police portal\n\nI am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters."
            }
        ]
    }
    
    with open('legal_knowledge_base.json', 'w') as f:
        json.dump(legal_db, f, indent=4)

# Lets load Legal jargon simplification dictionary
LEGAL_JARGON = {
    "cognizable offense": "crimes where police can arrest without a warrant",
    "non-cognizable offense": "crimes where police need court permission to arrest",
    "bail": "temporary release during trial proceedings",
    "anticipatory bail": "bail obtained in anticipation of arrest",
    "habeas corpus": "legal order to bring a detained person to court",
    "affidavit": "written statement confirmed by oath",
    "plaintiff": "person who initiates a lawsuit",
    "defendant": "person against whom legal action is brought",
    "deposition": "recorded testimony under oath",
    "jurisdiction": "authority of a court to hear a case",
    "suo moto": "action taken by a court on its own initiative",
    "writ petition": "court application for an order directing someone to act/not act",
    "respondent": "person who answers a court petition",
    "petitioner": "person who files a formal petition in court",
    "decree": "formal court order",
    "acquittal": "court declaration that someone is not guilty",
    "stay order": "court order to temporarily stop a proceeding",
    "adjournment": "postponement of court proceedings",
    "caveat": "notice submitted to prevent actions without informing the person",
    "injunction": "court order prohibiting someone from doing something",
    "quash": "to legally invalidate or void",
    "remand": "return a case to a lower court for further action",
    "ex-parte": "legal proceeding conducted with only one party present",
    "tort": "civil wrong that causes harm or loss",
    "declaration": "court judgment that establishes rights without ordering any action",
    "plaint": "written statement of a plaintiff's claim",
    "subpoena": "court order to appear or produce documents",
    "vacate": "to cancel or nullify a court order",
    "undertaking": "formal promise given to a court"
}

DOCUMENT_TEMPLATES = {
    "police_complaint": {
        "title": "Police Complaint Template",
        "template": """To,
The Station House Officer,
{police_station} Police Station,
{police_station_address}

Subject: Complaint regarding {complaint_subject}

Respected Sir/Madam,

I, {complainant_name}, resident of {complainant_address}, wish to report the following incident:

Date of Incident: {incident_date}
Time of Incident: {incident_time}
Place of Incident: {incident_place}

Details of the incident:
{incident_details}

Names and details of persons involved (if known):
{persons_involved}

Names and contact details of witnesses (if any):
{witnesses}

I request you to register my complaint and take appropriate action as per law.

Yours sincerely,
{complainant_name}
Contact: {complainant_phone}
Date: {current_date}
"""
    },
    "rti_application": {
        "title": "RTI Application Template",
        "template": """To,
The Public Information Officer,
{department_name},
{department_address}

Subject: Application under Right to Information Act, 2005

Respected Sir/Madam,

I, {applicant_name}, resident of {applicant_address}, wish to seek information under the Right to Information Act, 2005.

The details of the information sought are as follows:
{information_sought}

Period for which information is sought: {information_period}

I state that the information sought does not fall within the restrictions contained in Section 8 and 9 of the RTI Act and to the best of my knowledge it pertains to your department.

A fee of Rs. 10/- has been deposited vide receipt number {receipt_number} dated {receipt_date} / is enclosed herewith as IPO/DD.

Yours faithfully,
{applicant_name}
Address: {applicant_address}
Phone: {applicant_phone}
Date: {current_date}
"""
    },
    "consumer_complaint": {
        "title": "Consumer Complaint Template",
        "template": """To,
The District Consumer Disputes Redressal Forum,
{district}, {state}

Subject: Complaint under the Consumer Protection Act, 2019

Complainant:
{complainant_name}
{complainant_address}
{complainant_phone}

Opposite Party:
{seller_name}
{seller_address}
{seller_phone}

COMPLAINT

1. Details of transaction:
   Date of purchase/service: {transaction_date}
   Amount paid: Rs. {amount_paid}
   Mode of payment: {payment_mode}
   Receipt/Invoice number: {receipt_number}

2. Details of the product/service:
   {product_details}

3. Complaint details:
   {complaint_details}

4. Deficiency in service/defect in goods:
   {deficiency_details}

5. Steps taken to resolve the issue with the opposite party:
   {resolution_attempts}

6. Relief sought:
   {relief_sought}

7. Declaration:
   I/We declare that the information given above is true to the best of my/our knowledge and belief.

Place: {place}
Date: {current_date}

Signature of the Complainant
{complainant_name}

Attachments:
1. Copy of bill/receipt
2. Copy of correspondence with opposite party
3. Samples/photographs (if applicable)
"""
    },
    "rent_agreement": {
        "title": "Rent Agreement Template",
        "template": """RENT AGREEMENT

This Rent Agreement is made on this {agreement_date} between:

LANDLORD:
{landlord_name}
{landlord_address}
{landlord_phone}

AND

TENANT:
{tenant_name}
{tenant_address}
{tenant_phone}

1. PREMISES:
   The Landlord agrees to rent to the Tenant the property located at:
   {property_address}

2. TERM:
   The term of this Agreement shall be for a period of {agreement_duration}, commencing from {start_date} and ending on {end_date}.

3. RENT:
   The monthly rent shall be Rs. {monthly_rent}/- payable in advance on or before the {rent_due_date} day of each month.

4. SECURITY DEPOSIT:
   The Tenant has paid a security deposit of Rs. {security_deposit}/- which will be refunded at the time of vacating the premises after deducting any damages or dues.

5. MAINTENANCE:
   The Tenant shall maintain the premises in good condition. Normal wear and tear is expected.

6. UTILITIES:
   {utilities_clause}

7. TERMINATION:
   Either party may terminate this Agreement by giving {notice_period} notice in writing.

8. RESTRICTIONS:
   {restrictions}

9. OTHER TERMS:
   {other_terms}

IN WITNESS WHEREOF, the parties have executed this Agreement on the date first above written.

_________________                 _________________
Landlord Signature                Tenant Signature

Witnesses:
1. Name: {witness1_name}
   Address: {witness1_address}
   Signature: _________________

2. Name: {witness2_name}
   Address: {witness2_address}
   Signature: _________________
"""
    }
}

# Legal timelines data
LEGAL_TIMELINES = {
    "fir_to_chargesheet": [
        {"step": "File FIR", "timeframe": "Day 1", "details": "Visit police station with jurisdiction"},
        {"step": "Police Investigation", "timeframe": "Day 1-90", "details": "Collection of evidence, statements"},
        {"step": "Arrest (if applicable)", "timeframe": "Varies", "details": "Based on evidence gathering"},
        {"step": "Chargesheet Filing", "timeframe": "Within 90 days", "details": "For serious offenses (60 days for less serious)"},
        {"step": "Court Proceedings", "timeframe": "After chargesheet", "details": "Trial begins after chargesheet"}
    ],
    "consumer_complaint_process": [
        {"step": "Written Complaint to Business", "timeframe": "Day 1", "details": "First attempt at resolution"},
        {"step": "Wait for Response", "timeframe": "15-30 days", "details": "Allow reasonable time for response"},
        {"step": "File Complaint with Consumer Forum", "timeframe": "After trying resolution", "details": "Submit required documents and fee"},
        {"step": "Notice to Opposite Party", "timeframe": "Within 21 days", "details": "Forum sends notice to business"},
        {"step": "Response from Opposite Party", "timeframe": "Within 30 days", "details": "Business submits their response"},
        {"step": "Hearing", "timeframe": "Scheduled by Forum", "details": "Both parties present their case"},
        {"step": "Order/Judgment", "timeframe": "Typically 3-6 months", "details": "Decision by the Consumer Forum"}
    ],
    "civil_case_procedure": [
        {"step": "Filing Plaint", "timeframe": "Day 1", "details": "Submit case to appropriate court with fees"},
        {"step": "Scrutiny & Registration", "timeframe": "7-14 days", "details": "Court checks for defects and registers"},
        {"step": "Summons to Defendant", "timeframe": "Within 30 days", "details": "Court notifies the opposite party"},
        {"step": "Filing Written Statement", "timeframe": "30-90 days", "details": "Defendant responds to allegations"},
        {"step": "Framing of Issues", "timeframe": "Next hearing", "details": "Court defines points of contention"},
        {"step": "Evidence Submission", "timeframe": "Multiple hearings", "details": "Documents and witness testimony"},
        {"step": "Final Arguments", "timeframe": "After evidence", "details": "Lawyers present final case"},
        {"step": "Judgment", "timeframe": "Typically 1-3 years", "details": "Court gives final decision"},
        {"step": "Execution", "timeframe": "If judgment not followed", "details": "Enforcement of court order"}
    ]
}