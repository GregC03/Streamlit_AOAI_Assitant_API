#from openai import OpenAI
import streamlit as st
from utils import get_assistant_response, upload_files
import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

CHATBOT_NAME = "Test Chatbot"
#OPENAI_API_KEY = st.secrets["AZURE_OPENAI_API_KEY"]
#ASSISTANT_ID = st.secrets["ASST_ID"]
#ACCEPTED_FILE_TYPES = ["pdf", "txt", "png", "jpeg", "jpg"]

#client = OpenAI(api_key=OPENAI_API_KEY)
#assistant = client.beta.assistants.retrieve(ASSISTANT_ID)

client = AzureOpenAI(
    api_key = os.getenv("AZURE_OPENAI_KEY"),  
    api_version = "2024-02-15-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_BASE")  # Use AZURE_OPENAI_BASE instead of AZURE_OPENAI_ENDPOINT
)

# Create an assistant
assistant = client.beta.assistants.create(
    name="Data Extraction from files",
    model = os.getenv("AZURE_OPENAI_MODEL"),
    instructions=f"You are a helpful AI assistant who extracts meaningful data from files folloring the instructions of the user." 
    f"You have access to a sandboxed environment for writing and testing code."
    f"When you are asked to to extract data from a file you should follow these steps:"
    f"1. Write the code to read the file uploaded by the user."
    f"2. Anytime you write new code display a preview of the code to show your work."
    f"3. Run the code to confirm that it runs."
    f"4. If the code is successful try to understand where the requested meaningful information is located in the file, for instance, if the file is an excel file the information could be located in a specific table inside a specific sheet. If the file is a PDF it may be in a specifc section of the document. If the file is a powerpoint it may be in a specific slide. If and only if you are not sure where the information is located in the file ask the user for more information."
    f"5. If the code is unsuccessful display the error message and try to revise the code and rerun going through the steps from above again."
    f"6. Once you have located the information display the information to the user."
    f"7. Then write the code to export the information to a file of the format requested by the user and display a preview of the code to show your work."
    f"8. Run the code to confirm that it runs."
    f"9. If the code is unsuccessful display the error message and try to revise the code and rerun going through the steps from above again."
    f"10. Once the code is successful run it and generate the file with the extracted information and display the file to the user.",
    tools=[{"type": "code_interpreter"}],
    #model="gpt-4-1106-preview" #You must replace this value with the deployment name for your model.
)

st.title(CHATBOT_NAME)

if "thread" not in st.session_state:
    st.session_state["thread"] = client.beta.threads.create()

if "messages" not in st.session_state:
    st.session_state.messages = []

# This will load initial messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Upload files form (this moves as chat messages adds up... You should fix it)
with st.form("Files form", clear_on_submit=True):
    uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True)#, type=ACCEPTED_FILE_TYPES)
    submitted = st.form_submit_button("Attach")

    if submitted:
        st.write("Files attached to next message! Type something!")

prompt = st.chat_input("Write your message here...")

if prompt:
    OpenAI_files = []
    if uploaded_files:
        OpenAI_files = upload_files(client, uploaded_files)

    st.session_state.messages.append({"role": "user", "content": prompt, "OpenAI_files": OpenAI_files})
    with st.chat_message("user"):
        st.markdown(prompt)
        st.write(f"Attached files: {', '.join([OpenAI_file.filename for OpenAI_file in OpenAI_files])}")

    with st.chat_message("assistant"):
        file_ids = [OpenAI_file.id for OpenAI_file in OpenAI_files]
        response = get_assistant_response(prompt, client, assistant, st.session_state.thread, file_ids)
        st.markdown(response)

    # The assistant never outputs files
    st.session_state.messages.append({"role": "assistant", "content": response, "file_ids": []})

    # Reset uploaded_files to None after processing the user's message
    st.session_state.uploaded_files = None
