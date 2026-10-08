import smtplib
import time
from email.message import EmailMessage

import streamlit as st
from google import genai
from google.genai import types

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Deadline Tracker",
    page_icon="📅",
    layout="wide",
)


# ============================================================
# CUSTOM UI STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       MAIN PAGE
       ====================================================== */

    .stApp {
        background: #f7f9fc;
        color: #111827;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }


    /* ======================================================
       HEADER
       ====================================================== */

    .main-header {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        padding: 28px 32px;
        border-radius: 20px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.18);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.1rem;
        font-weight: 700;
        color: white !important;
    }

    .main-header p {
        margin: 7px 0 0 0;
        opacity: 0.95;
        font-size: 1rem;
        color: white !important;
    }


    /* ======================================================
       INFO CARDS
       ====================================================== */

    .info-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 18px;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.04);
    }

    .info-card-title {
        font-size: 0.85rem;
        color: #6b7280 !important;
        margin-bottom: 5px;
    }

    .info-card-value {
        font-size: 1.05rem;
        font-weight: 600;
        color: #111827 !important;
    }


    /* ======================================================
       SECTION HEADING
       ====================================================== */

    .section-title {
        font-size: 1.15rem;
        font-weight: 650;
        color: #111827 !important;
        margin-top: 10px;
        margin-bottom: 12px;
    }


    /* ======================================================
       BUTTONS
       ====================================================== */

    div.stButton > button {
        border-radius: 12px;
        font-weight: 600;
        min-height: 44px;
    }


    /* ======================================================
       CHAT INPUT
       ====================================================== */

    [data-testid="stChatInput"] {
        border-radius: 16px;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    section[data-testid="stSidebar"] * {
        color: #111827 !important;
    }

    section[data-testid="stSidebar"] a {
        color: #2563eb !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #e5e7eb;
    }


    /* ======================================================
       CHAT MESSAGE TEXT
       ====================================================== */

    [data-testid="stChatMessage"] {
        color: #111827 !important;
    }

    [data-testid="stChatMessage"] p {
        color: #111827 !important;
    }

    [data-testid="stChatMessage"] li {
        color: #111827 !important;
    }

    [data-testid="stChatMessage"] strong {
        color: #111827 !important;
    }


    /* ======================================================
       GENERAL TEXT
       ====================================================== */

    .stMarkdown {
        color: #111827;
    }

    .stMarkdown p {
        color: #111827;
    }

    label {
        color: #111827 !important;
    }


    /* ======================================================
       FOOTER
       ====================================================== */

    .app-footer {
        text-align: center;
        color: #6b7280 !important;
        font-size: 0.8rem;
        margin-top: 30px;
        padding-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

MODEL_NAME = "gemini-3.8-flash"


# ============================================================
# GEMINI CLIENT
# ============================================================

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# ============================================================
# ONBOARDING
# ============================================================

if "onboarded" not in st.session_state:

    st.markdown(
        """
        <div class="main-header">
            <h1>📅 Deadline Tracker</h1>
            <p>Snap it. Track it. Stay ahead.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-title">YOUR ACADEMIC ASSISTANT</div>
            <div class="info-card-value">
                Upload a syllabus, assignment sheet, or timetable
                and let AI find the important deadlines for you.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name",
            placeholder="Enter your name",
        )

        email = st.text_input(
            "Your email address",
            placeholder="you@example.com",
        )

        submitted = st.form_submit_button(
            "Let's get started 🚀",
            use_container_width=True,
        )

    if submitted:

        if not name.strip() or not email.strip():

            st.warning(
                "Please fill in both your name and email address."
            )

        elif "@" not in email or "." not in email.split("@")[-1]:

            st.warning(
                "Please enter a valid email address."
            )

        else:

            st.session_state.name = name.strip()
            st.session_state.email = email.strip()

            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
            )

            st.session_state.messages = []

            st.session_state.deadline_results = []

            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# ============================================================
# SESSION STATE SAFETY
# ============================================================

if "deadline_results" not in st.session_state:
    st.session_state.deadline_results = []


# ============================================================
# MESSAGE DISPLAY
# ============================================================

def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content,
        }
    )

    render_message(st.session_state.messages[-1])


# ============================================================
# GEMINI REQUEST
# ============================================================

def ask_gemini(parts):

    max_retries = 3

    for attempt in range(max_retries):

        try:

            return st.session_state.chat.send_message(parts).text

        except Exception as error:

            error_message = str(error)

            # ------------------------------------------------
            # Temporary Gemini overload
            # ------------------------------------------------

            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
            ):

                if attempt < max_retries - 1:

                    time.sleep(2 ** attempt)
                    continue

                return (
                    "Gemini is temporarily busy right now. "
                    "Please try again in a moment."
                )

            # ------------------------------------------------
            # Gemini free-tier quota exceeded
            # ------------------------------------------------

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):

                return (
                    "Gemini's current free-tier limit has been "
                    "reached. Please try again later."
                )

            # ------------------------------------------------
            # Other unexpected errors
            # ------------------------------------------------

            return (
                f"Sorry, something went wrong: {error_message}"
            )


# ============================================================
# EMAIL SENDING
# ============================================================

def send_email(to_email, subject, body):

    try:

        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = st.secrets["GMAIL_ADDRESS"]
        message["To"] = to_email

        message.set_content(body)

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
        ) as server:

            server.login(
                st.secrets["GMAIL_ADDRESS"],
                st.secrets["GMAIL_APP_PASSWORD"],
            )

            server.send_message(message)

        return True, "Email sent successfully."

    except Exception as error:

        return False, str(error)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 📅 Deadline Tracker")

    st.markdown("---")

    st.markdown(
        f"""
        **Student**

        {st.session_state.name}
        """
    )

    st.markdown(
        f"""
        **Email**

        {st.session_state.email}
        """
    )

    st.markdown("---")

    st.markdown("### How it works")

    st.markdown(
        """
        **1. Upload**  
        Add a syllabus, timetable, or assignment image.

        **2. Extract**  
        Gemini identifies academic deadlines and important details.

        **3. Track**  
        Continue chatting about the deadlines.

        **4. Email**  
        Send your extracted deadline information directly to your inbox.
        """
    )

    st.markdown("---")

    st.caption("AI-powered academic deadline assistant")


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    f"""
    <div class="main-header">
        <h1>📅 Deadline Tracker</h1>
        <p>
            Your academic deadlines, organized in one place.
            Welcome back, {st.session_state.name}.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# EMAIL SUMMARY BUTTON
# ============================================================

email_col, status_col = st.columns(
    [1, 2],
    vertical_alignment="center",
)

with email_col:

    if st.button(
        "📧 Email My Deadline Summary",
        use_container_width=True,
    ):

        if not st.session_state.deadline_results:

            st.warning(
                "Upload a document or ask about a deadline first."
            )

        else:

            email_body = (
                f"Your Deadline Tracker Summary\n"
                f"{'=' * 32}\n\n"
                f"Hi {st.session_state.name},\n\n"
                f"Here are the deadline details identified "
                f"by Deadline Tracker:\n\n"
            )

            for index, result in enumerate(
                st.session_state.deadline_results,
                start=1,
            ):

                email_body += (
                    f"DEADLINE {index}\n"
                    f"{'-' * 20}\n"
                    f"{result}\n\n"
                )

            email_body += (
                "Stay organized and don't miss your deadlines!\n\n"
                "— Deadline Tracker"
            )

            success, info = send_email(
                st.session_state.email,
                "Your Deadline Tracker Summary",
                email_body,
            )

            if success:

                st.success(
                    "Your deadline summary has been emailed! 📧"
                )

            else:

                st.error(
                    f"Couldn't send the email: {info}"
                )

with status_col:

    if st.session_state.deadline_results:

        st.caption(
            "✓ Deadline information is ready to be emailed."
        )

    else:

        st.caption(
            "Upload an academic document to get started."
        )


# ============================================================
# SECTION TITLE
# ============================================================

st.markdown(
    '<div class="section-title">💬 Your Deadline Assistant</div>',
    unsafe_allow_html=True,
)


# ============================================================
# WELCOME MESSAGE / CHAT HISTORY
# ============================================================

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        ),
    )

else:

    for message in st.session_state.messages:

        render_message(message)


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask about a deadline, or attach a photo",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
    ],
)


# ============================================================
# PROCESS USER INPUT
# ============================================================

if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes,
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    if text:

        add_message(
            "user",
            "text",
            text,
        )

        parts.append(text)


    # --------------------------------------------------------
    # PHOTO WITHOUT TEXT
    # --------------------------------------------------------

    elif photo is not None:

        parts.append(
            "Extract all academic deadlines from this document. "
            "For each deadline, give the task or event, the date, "
            "and any important relevant details. "
            "Do not guess or invent missing dates."
        )


    # --------------------------------------------------------
    # GEMINI RESPONSE
    # --------------------------------------------------------

    with st.spinner(
        "Reading your deadlines..."
    ):

        answer = ask_gemini(parts)


    add_message(
        "assistant",
        "text",
        answer,
    )


    # --------------------------------------------------------
    # SAVE ONLY REAL AI RESULTS FOR EMAIL
    # --------------------------------------------------------

    if not (
        answer.startswith("Gemini's current free-tier")
        or answer.startswith("Gemini is temporarily busy")
        or answer.startswith("Sorry, something went wrong")
    ):

        st.session_state.deadline_results.append(
            answer
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="app-footer">
        Deadline Tracker • AI-powered academic organization
    </div>
    """,
    unsafe_allow_html=True,
)