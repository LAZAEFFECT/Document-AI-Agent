import streamlit as st
import requests
import gspread
from fpdf import FPDF  # ✅ Correct import
import smtplib
import os
from email.message import EmailMessage
import zipfile  # built-in, no install needed

# --- Secure Configuration using Streamlit Secrets ---
# Store these in Streamlit Cloud: Settings > Secrets
import streamlit as st

# Load secrets from Streamlit
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]


# Define the local path for the DejaVuSans font file
# Make sure DejaVuSans.ttf is in the same directory as app.py
dejavu_font_local_path = 'DejaVuSans.ttf'

# --- Core Functions (from Colab notebook) ---

def send_email_pdf(to_email, client_name, filename, pdf_data):
    """Sends an email with a PDF attachment."""
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = f"Your Document – {client_name}"

    html_content = f"""
    <html>
    <body>
        <p>Hi {client_name},</p>
        <p>Please find your document attached.</p>
        <p>Best,</p>
        <p>Pretoria AI</p>
    </body>
    </html>
    """
    msg.add_alternative(html_content, subtype='html')
    msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=filename)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)

MODEL_NAME = "openrouter/gpt-4o-mini"

def generate_document_from_api(prompt):
    """Calls OpenRouter API using gpt-4o-mini to generate document content."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openrouter/gpt-4o-mini",
        "input": prompt
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/completions", headers=headers, json=payload)
        response.raise_for_status()
        # gpt-4o-mini returns generated text in 'output_text' key
        text = response.json().get("output_text", "")
        if not text:
            return None, "No output returned from API."
        return text, None

    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error: {e} | Status code: {response.status_code} | Response: {response.text}"
    except requests.exceptions.RequestException as e:
        return None, f"API request failed: {e}"

def create_pdf(text_content, font_path):
    """Creates a PDF from the given text content using a specified font."""
    pdf = FPDF()
    pdf.add_page()
    if font_path and os.path.exists(font_path):
        try:
            pdf.add_font('DejaVuSans', '', font_path, uni=True)
            pdf.set_font("DejaVuSans", size=12)
        except Exception as e:
            st.warning(f"Could not load specified font {font_path}. Falling back to Arial. Error: {e}")
            pdf.set_font("Arial", size=12)
            # Attempt to handle potential encoding issues by replacing unsupported characters
            text_content = text_content.encode('latin-1', 'replace').decode('latin-1')
    else:
        st.warning("Font file not found at specified path. Using default Arial font. Unicode characters may not render correctly.")
        pdf.set_font("Arial", size=12)
        # Attempt to handle potential encoding issues by replacing unsupported characters
        text_content = text_content.encode('latin-1', 'replace').decode('latin-1')

    pdf.multi_cell(190, 8, text_content)
    return pdf.output(dest='S').encode('latin-1')


# --- Streamlit App UI ---

st.title("📄 Document Agent for Small Businesses")

st.info("This tool generates professional documents like invoices and contracts. Fill in the details below and click 'Generate Document'.")

# --- User Inputs ---
with st.form("document_form"):
    client_name = st.text_input("Client's Full Name", placeholder="e.g., John Doe")
    client_email = st.text_input("Client's Email Address", placeholder="e.g., john.doe@example.com")
    business_name = st.text_input("Business Name (Optional)", placeholder="e.g., Doe's Digital Solutions")
    request_type = st.selectbox("Select Document Type", ["Invoice", "Contract"], index=0)
    description = st.text_area("Description & Notes", placeholder="Provide all necessary details for the document. \nFor an invoice, include services, quantities, and prices (e.g., 'Web design - R5000, Logo - R1500'). \nFor a contract, describe the services, terms, and duration.")

    submitted = st.form_submit_button("Generate & Email Document")


# --- Main Processing Logic ---
if submitted:
    if not client_name or not client_email or not description:
        st.error("Please fill in all required fields: Client's Name, Email, and Description.")
    else:
        with st.spinner(f"Generating {request_type.lower()} for {client_name}..."):
            # 1. Construct the prompt
            prompt_templates = {
    "invoice": """
You are an AI assistant that generates professional invoices.

Client Name: {client_name}
Business Name: {business_name}
Details: {description}

Instructions:
- Create a unique Invoice Number and use today's date.
- List items with prices, calculate subtotal, a 15% VAT, and a final total.
- Format it clearly as an invoice.
- Do NOT include placeholders like '[Your Company Name]'.

Output the full invoice as plain text, ready to copy into a PDF.
""",
    "contract": """
You are an AI assistant that generates formal service agreements.

Client Name: {client_name}
Business Name: {business_name}
Core Agreement Details: {description}

Instructions:
- Include clauses for Services, Compensation, Term, Confidentiality, and Termination.
- Format it clearly as a contract.
- Do NOT include placeholders for signatures.
- Output the full contract as plain text, ready to copy into a PDF.
"""
}
            prompt = prompt_templates[request_type.lower()].format(
                client_name=client_name,
                business_name=business_name if business_name else client_name,
                description=description
            )

            # 2. Generate document content
            st.write("Step 1: Calling AI to generate document text...")
            generated_text, error = generate_document_from_api(prompt)

            if error:
                st.error(f"Failed to generate document. {error}")
            else:
                st.success("Document text generated successfully.")
                st.write("Step 2: Creating PDF...")

                # 3. Create PDF
                # Pass the font path to the create_pdf function
                pdf_data = create_pdf(generated_text, dejavu_font_local_path)
                st.success("PDF created successfully.")
                st.write("Step 3: Sending email...")

                # 4. Send Email
                filename = f"{client_name.replace(' ', '_')}_{request_type.lower()}.pdf"
                email_sent, email_error = send_email_pdf(client_email, client_name, filename, pdf_data)

                if email_sent:
                    st.balloons()
                    st.success(f"✅ Successfully generated and emailed the {request_type} to {client_email}!")
                    st.subheader("Generated Document Preview:")
                    st.text_area("Content", generated_text, height=300)
                else:
                    st.error(f"Failed to send email. {email_error}")
