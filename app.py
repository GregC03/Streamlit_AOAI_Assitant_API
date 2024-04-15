#from openai import OpenAI
import streamlit as st
from utils import get_assistant_response, upload_files
import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

CHATBOT_NAME = "Relevant Data extractor from any file to .txt"

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
    f"Hai accesso a un ambiente sandbox per scrivere e testare il codice (code interpreter) e puoi chiamare funzioni."
    f"Quando ti viene chiesto di estrarre dati da un file, dovresti seguire questi passaggi:"
    f"1. Scrivi il codice per leggere il file caricato dall'utente."
    f"2. Ogni volta che scrivi un nuovo codice, visualizza un'anteprima del codice per mostrare il tuo lavoro."
    f"3. Esegui il codice per confermare che funzioni."
    f"4. Se il codice ha successo, cerca di capire dove si trova l'informazione significativa richiesta nel file, ad esempio, se il file è un file Excel, le informazioni potrebbero trovarsi in una tabella specifica all'interno di un foglio specifico. Se il file è un PDF, potrebbe trovarsi in una sezione specifica del documento. Se il file è una presentazione, potrebbe trovarsi in una diapositiva specifica. Se e solo se non sei sicuro di dove si trovi l'informazione nel file, chiedi all'utente maggiori informazioni."
    f"5. Se il codice non ha successo, visualizza il messaggio di errore e cerca di rivedere il codice e rieseguirlo passando attraverso i passaggi di cui sopra di nuovo."
    f"6. Una volta individuata l'informazione, scrivi il codice per esportare l'informazione in un file del formato richiesto dall'utente e visualizza un'anteprima del codice per mostrare il tuo lavoro."
    f"7. Esegui il codice per confermare che funzioni."
    f"8. Se il codice non ha successo, visualizza il messaggio di errore e cerca di rivedere il codice e rieseguirlo passando attraverso i passaggi di cui sopra di nuovo."
    f"9. Una volta che il codice ha successo, eseguilo e salva il file di output."
    f"10. Scrivi le prime poche righe del file di output nella tua risposta e ricorda all'utente che può scaricare il file di output per visualizzare l'intero risultato.",
    tools=[{"type": "code_interpreter"}],    
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
with st.form("Files da", clear_on_submit=True):
    uploaded_files = st.file_uploader("Carica Files", accept_multiple_files=True)#, type=ACCEPTED_FILE_TYPES)
    submitted = st.form_submit_button("Allega")

    if submitted:
        st.write("File allegati al messaggio di testo, Scrivi la tua richiesta all'assistente! \n TESTING PURPOSE -> USE THIS PROMPT: Nel file .xlsx di input sono presenti dei requisiti per una RFP: trovali, estraili e scrivili in un file .txt con un requisito per ogni riga")

prompt = st.chat_input("Scrivi il tuo messaggio qui...")

if prompt:
    OpenAI_files = []
    if uploaded_files:
        OpenAI_files = upload_files(client, uploaded_files)

    st.session_state.messages.append({"role": "user", "content": prompt, "OpenAI_files": OpenAI_files})
    with st.chat_message("user"):
        st.markdown(prompt)
        st.write(f"Files allegati: {', '.join([OpenAI_file.filename for OpenAI_file in OpenAI_files])}")

    with st.chat_message("assistant"):
        file_ids = [OpenAI_file.id for OpenAI_file in OpenAI_files]
        response = get_assistant_response(prompt, client, assistant, st.session_state.thread, file_ids)

        st.markdown(response)

    # Download output

    # Get all the files in the main directory
    files = os.listdir()

    # Filter the files that contain the word "output"
    output_files = [file for file in files if "output" in file]
    for file in output_files:
        with open(file, "rb") as f:
            file_data = f.read()
        st.download_button(label=f"Scarica file ({file}) di output", data=file_data, file_name=file)

    # The assistant never outputs files
    st.session_state.messages.append({"role": "assistant", "content": response, "file_ids": file_ids})

    # Reset uploaded_files to None after processing the user's message
    st.session_state.uploaded_files = None

