import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Texas Guardianship Intake", layout="centered")

st.title("Guardianship Client Intake Form")
st.write("Please complete the following information to assist our firm with evaluating your guardianship matter under Texas law.")

def get_gspread_client():
    # Read Google credentials securely from Streamlit Secrets
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
        # Open Google Sheet by Name (File must exist in your Google Drive)
        sheet = client.open("Guardianship_Intake_Database").sheet1
        sheet.append_row(list(data_dict.values()))
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

data = {}
data['Submission_Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- SECTION 1: APPLICANT INFORMATION ---
st.header("1. Applicant Information")
data['Client_Full_Name'] = st.text_input("Client Full Name *")
col1, col2 = st.columns(2)
with col1:
    data['Client_Street_Address'] = st.text_input("Street Address *")
    data['Client_County'] = st.text_input("County *")
with col2:
    data['Client_City_State_Zip'] = st.text_input("City, State, Zip Code *")

data['Client_Relationship_to_Ward'] = st.text_input("Relationship to Proposed Ward * (e.g., Parent, Adult Child, Sibling)")
data['Is_Potential_Guardian'] = st.radio("Will you be applying to be appointed as the Guardian?", ["Yes", "No"])

# Statutory Felony Disqualification - Texas Estates Code § 1104.351
has_felony = st.radio("Have you ever been convicted of a felony under state or federal law?", ["No", "Yes"])

if has_felony == "Yes":
    st.error(
        "WARNING: UNDER TEXAS ESTATES CODE SECTION 1104.351, A PERSON CONVICTED OF A FELONY "
        "IS STATUTORILY DISQUALIFIED FROM BEING APPOINTED AS A GUARDIAN UNLESS THEIR RIGHTS HAVE BEEN "
        "RESTORED OR PERMITTED BY LAW. THERE IS A VERY HIGH CHANCE THAT THE COURT MAY NOT APPOINT "
        "YOU AS THE GUARDIAN. PLEASE STOP AND CONTACT OUR OFFICE DIRECTLY BEFORE PROCEEDING."
    )
    st.stop()

data['Client_SSN_Last3'] = st.text_input("Last 3 Digits of Social Security Number *", max_chars=3)
col3, col4 = st.columns(2)
with col3:
    data['Client_DL_Last3'] = st.text_input("Last 3 Digits of Driver's License Number *", max_chars=3)
with col4:
    data['Client_DL_State'] = st.text_input("Driver's License State of Issue *", value="TX")

# --- SECTION 2: PROPOSED WARD INFORMATION ---
st.header("2. Proposed Ward Information")
data['Ward_Full_Name'] = st.text_input("Proposed Ward's Full Name *")
col5, col6 = st.columns(2)
with col5:
    data['Ward_Res_Street'] = st.text_input("Residential Address *")
    data['Ward_Res_County'] = st.text_input("County of Residence *")
with col6:
    data['Ward_Res_City_State_Zip'] = st.text_input("City, State, Zip *")

data['Ward_Current_Location'] = st.text_input("Where is the Proposed Ward currently residing? (e.g., Home, Hospital, Assisted Living Facility)")

# --- SECTION 3: SCOPE OF GUARDIANSHIP ---
st.header("3. Scope of Guardianship")
has_assets = st.radio(
    "Does the Proposed Ward own real estate, bank accounts, investments, or significant personal property? (Excluding SS/VA benefits)",
    ["No", "Yes"]
)

if has_assets == "No":
    st.info("If the Proposed Ward has no assets or property, a Guardianship of the Estate is generally unnecessary. Form defaulting to Guardianship of the Person only.")
    data['Guardianship_Type_Needed'] = "Guardianship of the Person Only"
else:
    guard_type = st.radio(
        "Select required scope:",
        ["Guardianship of both Person and Estate", "Guardianship of the Estate Only", "Guardianship of the Person Only"]
    )
    data['Guardianship_Type_Needed'] = guard_type

# --- SECTION 4: FAMILY MEMBERS ---
st.header("4. Family & Next of Kin")
data['Spouse_Info'] = st.text_area("Spouse Name & Address")
data['Parents_Info'] = st.text_area("Parents' Names & Addresses")
data['Adult_Children_Info'] = st.text_area("Adult Children's Names & Addresses")
data['Adult_Siblings_Info'] = st.text_area("Adult Siblings' Names & Addresses")

# --- SUBMIT BUTTON ---
st.markdown("---")
if st.button("Submit Intake Information"):
    if not data['Client_Full_Name'] or not data['Ward_Full_Name']:
        st.warning("Please fill out all required fields marked with *.")
    else:
        if save_to_google_sheets(data):
            st.success("Information submitted successfully! Our office will review your file.")
