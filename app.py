import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import io
import zipfile
from docxtpl import DocxTemplate

st.set_page_config(page_title="Texas Guardianship Portal", layout="centered")

# ==========================================
# GOOGLE SHEETS CONNECTION SETUP
# ==========================================
def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

def fetch_intake_data():
    try:
        client = get_gspread_client()
        sheet = client.open("Guardianship_Intake_Database").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching data from Google Sheets: {e}")
        return pd.DataFrame()

def save_to_google_sheets(data_dict):
    try:
        client = get_gspread_client()
        sheet = client.open("Guardianship_Intake_Database").sheet1
        sheet.append_row(list(data_dict.values()))
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Client Intake Form", "Admin Document Generator"])

# ==========================================
# PAGE 1: CLIENT INTAKE FORM
# ==========================================
if page == "Client Intake Form":
    st.title("Guardianship Client Intake Form")
    st.write("Please complete the following information to assist our firm with evaluating your guardianship matter under Texas law.")

    data = {}
    data['Submission_Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Section 1: Applicant Information
    st.header("1. Applicant Information")
    data['Client_Full_Name'] = st.text_input("Client Full Name *")
    col1, col2 = st.columns(2)
    with col1:
        data['Client_Street_Address'] = st.text_input("Client Street Address *")
        data['Client_County'] = st.text_input("Client County *")
    with col2:
        data['Client_City_State_Zip'] = st.text_input("Client City, State, Zip Code *")

    data['Client_Relationship_to_Ward'] = st.text_input("Relationship to Proposed Ward *")
    data['Is_Potential_Guardian'] = st.radio("Will you be applying to be appointed as Guardian?", ["Yes", "No"])

    has_felony = st.radio("Have you ever been convicted of a felony under state or federal law?", ["No", "Yes"])
    if has_felony == "Yes":
        st.error("WARNING: UNDER TEXAS ESTATES CODE § 1104.351, A CONVICTED FELON IS STATUTORILY DISQUALIFIED. PLEASE CONTACT OUR OFFICE.")
        st.stop()

    col3, col4 = st.columns(2)
    with col3:
        data['Client_SSN_Last3'] = st.text_input("Applicant SSN (Last 3) *", max_chars=3)
    with col4:
        data['Client_DL_Last3'] = st.text_input("Applicant DL (Last 3) *", max_chars=3)

    # Section 2: Proposed Ward Information
    st.header("2. Proposed Ward Information")
    data['Ward_Full_Name'] = st.text_input("Proposed Ward Full Name *")
    data['Ward_DOB'] = st.text_input("Proposed Ward Date of Birth * (MM/DD/YYYY)")

    col5, col6 = st.columns(2)
    with col5:
        data['Ward_SSN_Last3'] = st.text_input("Ward SSN (Last 3) *", max_chars=3)
    with col6:
        data['Ward_DL_Last3'] = st.text_input("Ward DL (Last 3) *", max_chars=3)

    col7, col8 = st.columns(2)
    with col7:
        data['Ward_Res_Street'] = st.text_input("Ward Residential Address *")
        data['Ward_Res_County'] = st.text_input("Ward County of Residence *")
    with col8:
        data['Ward_Res_City_State_Zip'] = st.text_input("Ward City, State, Zip *")

    data['Ward_Current_Location'] = st.text_input("Where is the Ward CURRENTLY residing?")

    # Section 3: Incapacity
    st.header("3. Incapacity Details")
    data['Ward_Medical_Condition'] = st.text_area("Specific medical/physical conditions *")
    data['Ward_Impairment_Details'] = st.text_area("How does this condition prevent self-care? *")

    # Section 4: Less Restrictive Alternatives
    st.header("4. Less Restrictive Alternatives")
    alternatives = st.multiselect(
        "Check existing legal arrangements:",
        ["Statutory Durable POA", "Medical POA", "Supported Decision-Making Agreement", "Management Trust", "Rep Payee", "None"]
    )
    data['Existing_Alternatives'] = ", ".join(alternatives) if alternatives else "None"
    data['Why_Alternatives_Fail'] = st.text_area("Why are these alternatives insufficient/unfeasible? *")

    # Section 5: Scope
    st.header("5. Scope of Guardianship")
    has_assets = st.radio("Does the Ward own significant assets/real estate?", ["No", "Yes"])
    data['Guardianship_Type_Needed'] = "Guardianship of the Person Only" if has_assets == "No" else st.radio("Scope:", ["Guardianship of Person & Estate", "Guardianship of Person Only"])

    # Section 6: Family
    st.header("6. Statutory Next of Kin")
    data['Spouse_Info'] = st.text_area("Spouse: Name & Address")
    data['Parents_Info'] = st.text_area("Parents: Names & Addresses")
    data['Adult_Children_Info'] = st.text_area("Adult Children: Names & Addresses")
    data['Adult_Siblings_Info'] = st.text_area("Adult Siblings: Names & Addresses")

    if st.button("Submit Intake Information"):
        if not data['Client_Full_Name'] or not data['Ward_Full_Name']:
            st.warning("Please complete required fields marked with *.")
        else:
            if save_to_google_sheets(data):
                st.success("Intake submitted successfully!")

# ==========================================
# PAGE 2: ADMIN DOCUMENT GENERATOR (PROTECTED)
# ==========================================
elif page == "Admin Document Generator":
    st.title("Admin Document Assembly Portal")
    
    password = st.text_input("Enter Attorney/Staff Passcode:", type="password")
    if password != "macneillaw":
        st.info("Please enter the passcode to access document drafting.")
        st.stop()

    st.success("Authenticated.")
    
    df = fetch_intake_data()
    if df.empty:
        st.warning("No client submissions found in database.")
    else:
        client_options = [f"{row['Ward_Full_Name']} (Client: {row['Client_Full_Name']})" for idx, row in df.iterrows()]
        selected_client_str = st.selectbox("Select Client Intake to Draft:", client_options)
        
        selected_idx = client_options.index(selected_client_str)
        client_data = df.iloc[selected_idx].to_dict()

        st.subheader("Client Details Overview")
        st.json({
            "Ward Name": client_data.get("Ward_Full_Name"),
            "Client Name": client_data.get("Client_Full_Name"),
            "County": client_data.get("Ward_Res_County"),
            "Guardianship Type": client_data.get("Guardianship_Type_Needed")
        })

        st.markdown("---")
        st.subheader("Generate Pleading Packets")

        col1, col2 = st.columns(2)

        # OPTION A: PERSON ONLY PACKET
        with col1:
            st.markdown("### Person Only")
            if st.button("Generate Person Only Packet (.zip)"):
                try:
                    ward_name = client_data.get('Ward_Full_Name', 'Ward')
                    templates_to_process = [
                        ("templates/person/Application_Person.docx", f"01_Application_Guardianship_{ward_name}.docx"),
                        ("templates/person/Motion_AAL.docx", f"02_Motion_Appointment_AAL_{ward_name}.docx"),
                        ("templates/person/Order_AAL.docx", f"03_Order_Appointing_AAL_{ward_name}.docx"),
                        ("templates/person/Affidavit_1051.104.docx", f"04_Affidavit_Regarding_Notice_{ward_name}.docx"),
                        ("templates/person/Waiver_Notice.docx", f"05_Waiver_of_Notice_{ward_name}.docx"),
                        ("templates/person/Order_Guardianship.docx", f"06_Order_Appointing_Permanent_Guardian_{ward_name}.docx"),
                        ("templates/person/Oath.docx", f"07_Oath_of_Guardian_{ward_name}.docx")
                    ]

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for tpl_path, output_filename in templates_to_process:
                            doc = DocxTemplate(tpl_path)
                            doc.render(client_data)
                            doc_io = io.BytesIO()
                            doc.save(doc_io)
                            doc_io.seek(0)
                            zip_file.writestr(output_filename, doc_io.getvalue())

                    zip_buffer.seek(0)
                    st.download_button(
                        label="Download Person Packet (.zip)",
                        data=zip_buffer,
                        file_name=f"Guardianship_Person_Packet_{ward_name}.zip",
                        mime="application/zip"
                    )
                except Exception as e:
                    st.error(f"Error: {e}. Check files in 'templates/person/'.")

        # OPTION B: PERSON & ESTATE PACKET
        with col2:
            st.markdown("### Person & Estate")
            if st.button("Generate Person & Estate Packet (.zip)"):
                try:
                    ward_name = client_data.get('Ward_Full_Name', 'Ward')
                    templates_to_process = [
                        ("templates/person_and_estate/Application_Person_Estate.docx", f"01_Application_Guardianship_Person_and_Estate_{ward_name}.docx"),
                        ("templates/person/Motion_AAL.docx", f"02_Motion_Appointment_AAL_{ward_name}.docx"),
                        ("templates/person/Order_AAL.docx", f"03_Order_Appointing_AAL_{ward_name}.docx"),
                        ("templates/person/Affidavit_1051.104.docx", f"04_Affidavit_Regarding_Notice_{ward_name}.docx"),
                        ("templates/person/Waiver_Notice.docx", f"05_Waiver_of_Notice_{ward_name}.docx"),
                        ("templates/person_and_estate/Order_Guardianship_Person_Estate.docx", f"06_Order_Appointing_Permanent_Guardian_{ward_name}.docx"),
                        ("templates/person_and_estate/Inventory_Appraisement.docx", f"07_Inventory_Appraisement_{ward_name}.docx"),
                        ("templates/person_and_estate/Order_Approving_Inventory.docx", f"08_Order_Approving_Inventory_{ward_name}.docx"),
                        ("templates/person/Oath.docx", f"09_Oath_of_Guardian_{ward_name}.docx")
                    ]

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for tpl_path, output_filename in templates_to_process:
                            doc = DocxTemplate(tpl_path)
                            doc.render(client_data)
                            doc_io = io.BytesIO()
                            doc.save(doc_io)
                            doc_io.seek(0)
                            zip_file.writestr(output_filename, doc_io.getvalue())

                    zip_buffer.seek(0)
                    st.download_button(
                        label="Download Person & Estate Packet (.zip)",
                        data=zip_buffer,
                        file_name=f"Guardianship_Person_and_Estate_Packet_{ward_name}.zip",
                        mime="application/zip"
                    )
                except Exception as e:
                    st.error(f"Error: {e}. Check files in 'templates/person_and_estate/'.")
