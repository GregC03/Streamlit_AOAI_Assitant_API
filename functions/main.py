from openai import AzureOpenAI
import time
import json

def retrieve_file(client: AzureOpenAI):
    data = json.loads(messages.model_dump_json(indent=2))  # Load JSON data into a Python object
    file_id = data['data'][0]['content'][0]['file_id']
    content = client.files.content(file_id)

    return content

def write_file_to_temp(content: str, output_path: str):
    file_data_bytes = content.read()
    with open(output_path, 'w') as file:
        file.write(file_data_bytes)