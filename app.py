import streamlit as st
import requests
from fpdf2 import FPDF
import smtplib
import os
from email.message import EmailMessage

# --- Secure Configuration using Streamlit Secrets ---
# Store these in Streamlit Cloud: Settings > Secrets
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]

import streamlit as st
import requests

# --- Load secrets ---
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]

# --- DEBUG: Check OpenRouter account balance / status ---
st.subheader("🛠 OpenRouter Account Debug")
headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

try:
    response = requests.get("https://openrouter.ai/api/v1/account", headers=headers)
    response.raise_for_status()
    st.write("✅ Account info:", response.json())
except requests.exceptions.HTTPError as e:
    st.error(f"HTTP error: {e}")
    if response.text:
        st.text(f"Response: {response.text}")
except Exception as e:
    st.error(f"Other error: {e}")


# Local font path (ensure DejaVuSans.ttf is in your app folder)
dejavu_font_local_path = "DejaVuSans.ttf"


# --- Core Functions ---

def generate_document_from_api(prompt):
    """Call OpenRouter API (gpt-4o-mini) to generate document content."""
    url = "https://openrouter.ai/api/v1/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openrouter/gpt-4o-mini",
        "prompt": prompt,
        "max_tokens": 1000
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        text = data["completion"] if "completion" in data else data.get("choices", [{}])[0].get("text", "")
        return text, None
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error: {e} | Status code: {response.status_code} | Response: {response.text}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def create_pdf(text_content, font_path):
    """Creates a PDF from the given text content using a specified font."""
    pdf = FPDF()
    pdf.add_page()
    if font_path and os.path.exists(font_path):
        try:
            pdf.add_font("DejaVuSans", "", font_path, uni=True)
            pdf.set_font("DejaVuSans", size=12)
        except Exception as e:
            st.warning(f"Could not load specified font. Falling back to Arial. Error: {e}")
            pdf.set_font("Arial", size=12)
            text_content = text_content.encode("latin-1", "replace").decode("latin-1")
    else:
        st.warning("Font file not found. Using default Arial font.")
        pdf.set_font("Arial", size=12)
        text_content = text_content.encode("latin-1", "replace").decode("latin-1")

    pdf.multi_cell(190, 8, text_content)
    return pdf.output(dest="S").encode("latin-1")


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
        <p>Best regards,<br>Pretoria AI</p>
    </body>
    </html>
    """
    msg.add_alternative(html_content, subtype="html")
    msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=filename)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)


# --- Streamlit App UI ---
st.title("📄 Document Agent for Small Businesses")
st.info("Generate professional invoices or contracts and email them directly to clients.")

with st.form("document_form"):
    client_name = st.text_input("Client's Full Name", placeholder="e.g., John Doe")
    client_email = st.text_input("Client's Email Address", placeholder="e.g., john.doe@example.com")
    business_name = st.text_input("Business Name (Optional)", placeholder="e.g., Doe's Digital Solutions")
    request_type = st.selectbox("Select Document Type", ["Invoice", "Contract"])
    description = st.text_area(
        "Description & Notes",
        placeholder=(
            "Provide all necessary details for the document.\n"
            "Invoice example: 'Web design - R5000, Logo - R1500'.\n"
            "Contract example: 'Service duration 6 months, payment R5000/month'."
        )
    )

    submitted = st.form_submit_button("Generate & Email Document")


if submitted:
    if not client_name or not client_email or not description:
        st.error("Please fill in all required fields.")
    else:
        with st.spinner(f"Generating {request_type.lower()} for {client_name}..."):
            prompt_templates = {
                "Invoice": (
                    f"Generate a professional invoice for {client_name} of "
                    f"{business_name if business_name else client_name}.\n"
                    f"Details: {description}\n"
                    "- Create a unique Invoice Number and use today's date.\n"
                    "- List items with prices, calculate subtotal, a 15% VAT, and a final total.\n"
                    "- Do NOT include placeholders like '[Your Company Name]'."
                ),
                "Contract": (
                    f"Generate a formal service agreement between Pretoria AI and {client_name}.\n"
                    f"The core of the agreement is: {description}\n"
                    "- Include clauses for Services, Compensation, Term, Confidentiality, and Termination.\n"
                    "- Do NOT include placeholders for signatures."
                )
            }
            prompt = prompt_templates[request_type]

            # Generate document text
            generated_text, error = generate_document_from_api(prompt)

            if error:
                st.error(f"Failed to generate document. {error}")
            else:
                st.success("Document text generated successfully.")

                # Create PDF
                pdf_data = create_pdf(generated_text, dejavu_font_local_path)
                st.success("PDF created successfully.")

                # Send email
                filename = f"{client_name.replace(' ', '_')}_{request_type.lower()}.pdf"
                email_sent, email_error = send_email_pdf(client_email, client_name, filename, pdf_data)

                if email_sent:
                    st.balloons()
                    st.success(f"✅ {request_type} successfully emailed to {client_email}!")
                    st.subheader("Generated Document Preview:")
                    st.text_area("Content", generated_text, height=300)
                else:
                    st.error(f"Failed to send email. {email_error}")
