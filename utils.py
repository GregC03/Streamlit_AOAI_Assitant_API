from openai import OpenAI
from openai import AzureOpenAI
import time
import json
from streamlit.runtime.uploaded_file_manager import UploadedFile
from datetime import datetime
import random


from dotenv import load_dotenv
import os

load_dotenv()

CHATBOT_NAME = "Chatbot - Data extractor from files"

client = AzureOpenAI(
    api_key = os.getenv("AZURE_OPENAI_KEY"),  
    api_version = "2024-02-15-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_BASE")
)

try:
    from functions.main import *
except ImportError:
    print("No callable functions have been defined, you assistant should have no function calls as well")

DELAY = 0.1

def call_function(function_name: str, arguments):
    if function_name in globals() and callable(globals()[function_name]):
        function_to_call = globals()[function_name]
        return function_to_call(**arguments)
    else:
        raise ValueError(f"Function '{function_name}' does not exist")

def get_assistant_response(prompt, client: AzureOpenAI, assistant, thread, file_ids, prompt_counter):
    # Add user message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt,
        file_ids=file_ids
    )

    # Run the thread
    run = client.beta.threads.runs.create(
        thread_id = thread.id,
        assistant_id = assistant.id
    )

    # Check for status
    while True:
        time.sleep(DELAY)

        # Retrieve the run status
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        # If run is completed, get messages
        if run_status.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )

            break
        elif run_status.status == 'requires_action':
            
            if run_status.required_action.type == "submit_tool_outputs":
                required_actions = run_status.required_action.submit_tool_outputs.model_dump()
                tool_outputs = []

                for action in required_actions["tool_calls"]:
                    func_name = action['function']['name']
                    arguments = json.loads(action['function']['arguments'])

                    print(f"Calling Function {func_name} with arguments {arguments}")
                    
                    # This might create exception if the function is not defined
                    output = call_function(func_name, arguments)
                    tool_outputs.append({
                            "tool_call_id": action['id'],
                            "output": output
                        })
                    
                    
                print(f"Submitting outputs back to the Assistant: {tool_outputs}")
                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
        else:
            print("Waiting for the Assistant to process...")
    
    message = messages.data[0].content[-1]
    message_content = message.text
    annotations = message_content.annotations
    citations = list()

    for index, annotation in enumerate(annotations):

        message_content.value = message_content.value.replace(annotation.text, f"{{annotation_{index}}}")

        #if (file_citation := getattr(annotation, 'file_citation', None)):
        #    cited_file = client.files.retrieve(file_citation.file_id)
        #    citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
        #el
        if (file_path := getattr(annotation, 'file_path', None)):
            cited_file = client.files.retrieve(file_path.file_id)
            output_file = client.files.content(file_path.file_id)
            file_extension = cited_file.filename[cited_file.filename.find('.'):]
            output_path = f"./{str(datetime.now()).replace(' ', '_').replace(':', '-').replace('.', '_')}_output_{prompt_counter}{index}{file_extension}"
            with open(output_path, 'wb') as f:
                f.write(output_file.content)
            
            #message_content.value = message_content.value.replace(annotation.text, f"{{annotation_{index}}}")

            
            #citations.append(f'[{index}] Click <a href="./output_{index}.txt">{cited_file.filename}</a>')
            # Note: File download functionality not implemented above for brevity

    #message_content.value += '\n' + '\n'.join(citations)

    #message = messages.data[0].content[-1]
    #message = message.text.value
    print(f"Assistant Response: {messages}") # debug
    #return message
    return message_content.value

def upload_files(client: AzureOpenAI, files: list[UploadedFile]):
    AzureOpenAI_files = []

    for file in files:
        AzureOpenAI_files.append(client.files.create(file=file, purpose='assistants'))
    
    return AzureOpenAI_files


def download_buttons_sidebar():
    #download files
    @st.cache_data
    def read_file(file):
        with open(file, "rb") as f:
            return f.read()
    
    # Get all the files in the main directory
    files = os.listdir()
    
    # Filter the files that contain the word "output"
    output_files = [file for file in files if "output" in file]
    
    # Check if 'output_files_data' is already in the session state
    if 'output_files_data' not in st.session_state:
        st.session_state.output_files_data = {}
    
    # Read the files and store them in the session state
    for file in output_files:
        if file not in st.session_state.output_files_data:
            file_data = read_file(file)
            st.session_state.output_files_data[file] = file_data
    
    # Create download buttons in the sidebar from the session state
    for file, file_data in st.session_state.output_files_data.items():
        st.sidebar.download_button(label=f"Scarica file ({file}) di output", data=file_data, file_name=file, key=random.random())