Document Agent for Small Businesses
Overview
This project provides a Python-based Document Agent designed to help small businesses automate the generation of professional documents like invoices and contracts using AI. By providing client details and document requirements, the agent generates and emails the document as a PDF. The agent can be run as a Python script (e.g., in Google Colab) or deployed as a user-friendly web application using Streamlit.

Features
Generate invoices and contracts from structured data (e.g., Google Sheet).
Utilize an AI model (via OpenRouter API) for flexible document content generation based on descriptions.
Create professional PDF documents using fpdf2.
Upload generated PDFs to Google Drive.
Email generated PDFs to clients using Gmail SMTP.
Includes a basic Streamlit web application interface for easier use by non-technical users.
Enhanced error handling for better reliability.
Setup Requirements
To run this Document Agent, you will need:

A Google Account: Required for Google Sheets (if using the Colab version) and Gmail.
An OpenRouter API Key: Used to access the AI model. Obtain one from the OpenRouter website.
A Gmail Account with App Password: Used to send emails. Enable 2-factor authentication on your Gmail account and generate an App Password to use instead of your regular password.
A Unicode Font File (e.g., DejaVuSans.ttf): Required for generating PDFs with special characters. You may need to manually include this file in your environment or repository.
