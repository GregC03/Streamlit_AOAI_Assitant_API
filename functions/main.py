from openai import AzureOpenAI
import time
import json
import streamlit as st


import http.server
import socketserver



def retrieve_file(client: AzureOpenAI):
    data = json.loads(messages.model_dump_json(indent=2))  # Load JSON data into a Python object
    file_id = data['data'][0]['content'][0]['file_id']
    content = client.files.content(file_id)

    return content

def write_file_to_temp(content: str, output_path: str):
    file_data_bytes = content.read()
    with open(output_path, 'w') as file:
        file.write(file_data_bytes)


def https_download_link_creator(file_path: str):
    PORT = 8000

    Handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()

    return f"http://localhost:8000/{file_path}"