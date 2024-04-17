#from openai import OpenAI
import streamlit as st
from utils import get_assistant_response, upload_files, download_buttons_sidebar
import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv
from datetime import datetime
import random

load_dotenv()

CHATBOT_NAME = "Chatbot - Data extractor from files"


client = AzureOpenAI(
    api_key = os.getenv("AZURE_OPENAI_KEY"),  
    api_version = "2024-02-15-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_BASE")
)

# Create an assistant
assistant = client.beta.assistants.create(
    name="Assistente estrattore di dati rilevanti da file",
    #model="gpt-4-1106-preview", #You must replace this value with the deployment name for your model.
    model = os.getenv("AZURE_OPENAI_MODEL"),
    instructions=f"Sei un utile assistente AI che estrae dati significativi dai file seguendo le istruzioni dell'utente e restituisce quei dati all'utente."
    f"Hai accesso a un ambiente sandbox per scrivere e testare il codice (code interpreter)."
    f"Quando ti viene chiesto di estrarre dati da un file, devi seguire questi passaggi:"
    f"1. Scrivi il codice per leggere il file caricato dall'utente."
    f"2. Ogni volta che scrivi un nuovo codice, visualizza un'anteprima del codice per mostrare il tuo lavoro."
    f"3. Esegui il codice per confermare che funzioni."
    f"4. Se il codice ha successo, cerca di capire dove si trova l'informazione significativa richiesta nel file, ad esempio, se il file è un file Excel, le informazioni potrebbero trovarsi in una tabella specifica all'interno di un foglio specifico. Se il file è un PDF, potrebbe trovarsi in una sezione specifica del documento. Se il file è una presentazione, potrebbe trovarsi in una diapositiva specifica. Se e solo se non sei sicuro di dove si trovi l'informazione nel file, chiedi all'utente maggiori informazioni."
    f"5. Se il codice non ha successo, visualizza il messaggio di errore e cerca di rivedere il codice e rieseguirlo passando attraverso i passaggi di cui sopra di nuovo."
    f"6. Una volta individuata l'informazione, scrivi il codice per esportare l'informazione in un file del formato richiesto dall'utente e visualizza un'anteprima del codice per mostrare il tuo lavoro."
    f"7. Esegui il codice per confermare che funzioni."
    f"8. Se il codice non ha successo, visualizza il messaggio di errore e cerca di rivedere il codice e rieseguirlo passando attraverso i passaggi di cui sopra di nuovo."
    f"9. Una volta che il codice ha successo, eseguilo e salva il file di output."
    f"10. Mostra nella tua risposta un'anteprima delle informazioni contenute nel file di output e ricorda all'utente che può scaricare il file di output per visualizzare l'intero risultato.",
    tools=[{"type": "code_interpreter"}],    
)

st.title(CHATBOT_NAME)
st.write("Quando chiedi al bot di analizzare un file, scrivi nel prompt l'estensione del file (es. .xlsx) e il tipo di informazione che vuoi estrarre (es. requisiti per una RFP).")
st.sidebar.title("Files di output")
st.sidebar.markdown("Scarica i file di output qui (NON CLICCARE MENTRE IL CHATBOT E' IN RUN)")


if "thread" not in st.session_state:
    st.session_state["thread"] = client.beta.threads.create()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Upload files form
with st.form("Files da", clear_on_submit=True):
    uploaded_files = st.file_uploader("Carica Files", accept_multiple_files=True)#, type=ACCEPTED_FILE_TYPES)
    st.write(f"File già caricati: {', '.join([OpenAI_file.filename for OpenAI_file in st.session_state.uploaded_files])}")
    submitted = st.form_submit_button("Allega")

    if submitted:
        st.write("File allegati al messaggio di testo, Scrivi la tua richiesta all'assistente! \n \n \
                 SUGGESTED PROMPTS: Nel file .xlsx di input sono presenti dei requisiti per una RFP: trovali, estraili e scrivili in un file .txt con un requisito per ogni riga \n \n \
                 Nel file .xlsx di input sono presenti dei requisiti per una RFP: trovali, estraili e scrivili in un file .xlsx con ogni requisito in una cella diversa \n \n \
                 Nel file .xlsx di input sono presenti dei requisiti per una RFP: trovali, estraili e scrivili in un file .xlsx con ogni requisito in una cella diversa. Scrivili anche in un file .txt con un requisito per ogni riga")

# This will load initial messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Scrivi il tuo messaggio qui...")

download_buttons_sidebar()
if "prompt_counter" not in st.session_state:
    st.session_state.prompt_counter = 0

if prompt:
    st.session_state.prompt_counter += 1
     

    if uploaded_files:
        st.session_state.uploaded_files += upload_files(client, uploaded_files)
        uploaded_files = None
    
    OpenAI_files = st.session_state.uploaded_files

    st.session_state.messages.append({"role": "user", "content": prompt, "OpenAI_files": OpenAI_files})
    with st.chat_message("user"):
        st.markdown(prompt)
        st.write(f"Files allegati: {', '.join([OpenAI_file.filename for OpenAI_file in OpenAI_files])}")

    with st.chat_message("assistant"):
        file_ids = [OpenAI_file.id for OpenAI_file in OpenAI_files]
        response = get_assistant_response(prompt, client, assistant, st.session_state.thread, file_ids, st.session_state.prompt_counter)

        st.markdown(response)


    download_buttons_sidebar()

    # The assistant never outputs files
    st.session_state.messages.append({"role": "assistant", "content": response, "file_ids": file_ids})

    # Reset uploaded_files to None after processing the user's message
    st.session_state.uploaded_files = OpenAI_files

