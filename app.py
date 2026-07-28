import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Texas Guardianship Intake", layout="centered")

st.title("Guardianship Client Intake Form")
st.write("Please complete the following information to assist our firm with evaluating your guardianship matter under Texas law.")

def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

def save_to_google_sheets(data_dict):
    try:
        client = get_gspread_client()
        sheet = client.open("Guardianship_Intake_Database").sheet1
        sheet.append_row(list(data_dict.values()))
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

data = {}
data['Submission_Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ==========================================
# SECTION 1: APPLICANT INFORMATION
# ==========================================
st.header("1. Applicant Information")
data['Client_Full_Name'] = st.text_input("Client Full Name *")
col1, col2 = st.columns(2)
with col1:
    data['Client_Street_Address'] = st.text_input("Client Street Address *")
    data['Client_County'] = st.text_input("Client County *")
with col2:
    data['Client_City_State_Zip'] = st.text_input("Client City, State, Zip Code *")

data['Client_Relationship_to_Ward'] = st.text_input("Relationship to Proposed Ward * (e.g., Parent, Adult Child, Sibling)")
data['Is_Potential_Guardian'] = st.radio("Will you be applying to be appointed as the Guardian?", ["Yes", "No"])

# Statutory Felony Disqualification - Texas Estates Code § 1104.351
has_felony = st.radio("Have you ever been convicted of a felony under state or federal law?", ["No", "Yes"])
if has_felony == "Yes":
    st.error(
        "WARNING: UNDER TEXAS ESTATES CODE SECTION 1104.351, A PERSON CONVICTED OF A FELONY "
        "IS STATUTORILY DISQUALIFIED FROM BEING APPOINTED AS A GUARDIAN. THE COURT MAY NOT APPOINT "
        "YOU AS THE GUARDIAN. PLEASE STOP AND CONTACT OUR OFFICE DIRECTLY BEFORE PROCEEDING."
    )
    st.stop()

col3, col4 = st.columns(2)
with col3:
    data['Client_SSN_Last3'] = st.text_input("Applicant's Last 3 Digits of SSN *", max_chars=3)
with col4:
    data['Client_DL_Last3'] = st.text_input("Applicant's Last 3 Digits of Driver's License *", max_chars=3)

# ==========================================
# SECTION 2: PROPOSED WARD INFORMATION
# ==========================================
st.header("2. Proposed Ward Information")
data['Ward_Full_Name'] = st.text_input("Proposed Ward's Full Name *")
data['Ward_DOB'] = st.text_input("Proposed Ward's Date of Birth * (MM/DD/YYYY)")

col5, col6 = st.columns(2)
with col5:
    data['Ward_SSN_Last3'] = st.text_input("Ward's Last 3 Digits of SSN *", max_chars=3)
with col6:
    data['Ward_DL_Last3'] = st.text_input("Ward's Last 3 Digits of Driver's License *", max_chars=3)

col7, col8 = st.columns(2)
with col7:
    data['Ward_Res_Street'] = st.text_input("Ward's Residential Address *")
    data['Ward_Res_County'] = st.text_input("Ward's County of Residence * (Determines Venue)")
with col8:
    data['Ward_Res_City_State_Zip'] = st.text_input("Ward's City, State, Zip *")

data['Ward_Current_Location'] = st.text_input("Where is the Proposed Ward CURRENTLY residing? (e.g., Same as above, Hospital, Nursing Home)")

# ==========================================
# SECTION 3: INCAPACITY & MEDICAL CONDITIONS
# ==========================================
st.header("3. Incapacity Information")
st.write("To file an Application, the Court requires details on the Proposed Ward's physical and mental conditions.")

data['Ward_Medical_Condition'] = st.text_area("What specific mental or physical condition(s) cause the Proposed Ward's incapacity? * (e.g., Alzheimer's, Severe Autism, Traumatic Brain Injury)")
data['Ward_Impairment_Details'] = st.text_area("How does this condition prevent them from providing their own food, clothing, or shelter, or managing their own finances? *")

# ==========================================
# SECTION 4: LESS RESTRICTIVE ALTERNATIVES (TEC § 1101.001)
# ==========================================
st.header("4. Less Restrictive Alternatives")
st.write("Texas law requires the Court to determine if alternatives to guardianship were considered and why they are not feasible.")

alternatives = st.multiselect(
    "Check any legal documents or arrangements the Proposed Ward CURRENTLY has in place:",
    [
        "Statutory Durable Power of Attorney (Financial)",
        "Medical Power of Attorney",
        "Supported Decision-Making Agreement",
        "Management Trust / Special Needs Trust",
        "Representative Payee for Social Security/VA",
        "Joint Bank Accounts",
        "None of the Above"
    ]
)
# Convert list to comma-separated string for Google Sheets
data['Existing_Alternatives'] = ", ".join(alternatives) if alternatives else "None selected"

data['Why_Alternatives_Fail'] = st.text_area("If they have any of the above (or if they refuse to sign them), why are those alternatives INSUFFICIENT to protect the Proposed Ward? (e.g., They are actively being scammed, they revoke POAs, they lack capacity to sign POAs now)")

# ==========================================
# SECTION 5: SCOPE OF GUARDIANSHIP (Person vs. Estate)
# ==========================================
st.header("5. Scope of Guardianship")
has_assets = st.radio(
    "Does the Proposed Ward own real estate, bank accounts, investments, or significant personal property? (Do NOT count monthly Social Security / VA benefits)",
    ["No", "Yes"]
)
if has_assets == "No":
    st.info("Because there are no independent assets, a Guardianship of the Estate is likely unnecessary. Form defaulting to Guardianship of the Person only.")
    data['Guardianship_Type_Needed'] = "Guardianship of the Person Only"
else:
    data['Guardianship_Type_Needed'] = st.radio(
        "Select required scope:",
        ["Guardianship of both Person and Estate", "Guardianship of the Estate Only", "Guardianship of the Person Only"]
    )

# ==========================================
# SECTION 6: STATUTORY FAMILY MEMBERS (For Court Notice)
# ==========================================
st.header("6. Family & Next of Kin")
st.error("IMPORTANT: Texas law requires us to provide the Court with the complete mailing address for the following family members. Please provide FULL NAMES and COMPLETE MAILING ADDRESSES. If deceased, state 'Deceased'. If they have no children/siblings, state 'None'.")

data['Spouse_Info'] = st.text_area("Spouse: Name & Complete Mailing Address")
data['Parents_Info'] = st.text_area("Parents: Names & Complete Mailing Addresses")
data['Adult_Children_Info'] = st.text_area("Adult Children: Names & Complete Mailing Addresses")
data['Adult_Siblings_Info'] = st.text_area("Adult Siblings: Names & Complete Mailing Addresses")

# ==========================================
# SUBMIT BUTTON
# ==========================================
st.markdown("---")
if st.button("Submit Intake Information"):
    if not data['Client_Full_Name'] or not data['Ward_Full_Name'] or not data['Ward_Medical_Condition']:
        st.warning("Please fill out all required fields marked with *.")
    else:
        if save_to_google_sheets(data):
            st.success("Information submitted successfully! Our office will review your file.")
