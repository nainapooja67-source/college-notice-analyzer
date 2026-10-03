import os
import smtplib
from email.message import EmailMessage

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT, SUMMARY_REQUEST_PROMPT

load_dotenv()

st.set_page_config(
    page_title="AI College Notice Analyzer",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 AI College Notice Analyzer")
st.write(
    "Upload a college notice, get a clear AI-generated "
    "summary, and send it to your email."
)

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

uploaded_file = st.file_uploader(
    "Upload your college notice",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:
    image_bytes = uploaded_file.getvalue()

    st.image(
        image_bytes,
        caption="Uploaded college notice",
        use_container_width=True
    )

    if st.button("Analyze Notice", type="primary"):
        if not api_key:
            st.error("Gemini API key is missing in your .env file.")
        else:
            try:
                with st.spinner("Gemini is analyzing your notice..."):
                    client = genai.Client(api_key=api_key)

                    image_part = types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=uploaded_file.type
                    )

                    response = client.models.generate_content(
                        model=model_name,
                        contents=[
                            SYSTEM_PROMPT + "\n\n" +
                            SUMMARY_REQUEST_PROMPT,
                            image_part
                        ]
                    )

                    if not response.text:
                        st.error("Gemini did not return any text.")
                    else:
                        st.session_state["notice_summary"] = response.text

            except Exception as error:
                st.error(f"Could not analyze the notice: {error}")

summary = st.session_state.get("notice_summary")

if summary:
    st.subheader("📋 Notice Analysis")
    st.markdown(summary)

    st.download_button(
        "Download Summary",
        data=summary,
        file_name="college_notice_summary.txt",
        mime="text/plain"
    )

    st.divider()
    st.subheader("📧 Email the Summary")

    recipient_email = st.text_input(
        "Enter the recipient's email address"
    )

    if st.button("Send Email"):
        sender_email = os.getenv("SENDER_EMAIL")
        app_password = os.getenv("SENDER_APP_PASSWORD")

        if not sender_email or not app_password:
            st.error("Please configure your email settings in .env.")
        elif not recipient_email or "@" not in recipient_email:
            st.warning("Please enter a valid email address.")
        else:
            try:
                message = EmailMessage()
                message["Subject"] = "Your AI College Notice Summary"
                message["From"] = sender_email
                message["To"] = recipient_email

                message.set_content(
                    "Here is the AI-generated summary of your "
                    "college notice:\n\n" + summary
                )

                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(sender_email, app_password)
                    server.send_message(message)

                st.success("Summary emailed successfully!")

            except Exception as error:
                st.error(f"Email could not be sent: {error}")

if st.button("Clear and Upload Another Notice"):
    st.session_state.pop("notice_summary", None)
    st.rerun()