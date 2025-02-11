import os
import re
import ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from reader import make_reader
import os

from download import fetch_and_download
from parse import parse_html_to_txt_cna
from feed import getEntries, updateFeed
from dotenv import load_dotenv

load_dotenv('.env')

# Retrieve environment variables
RSS_URL = os.getenv("RSS_URL", "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml")
ENTRIES_DIR = os.getenv("ENTRIES_DIR", "entries")
HTML_DIR = os.getenv("HTML_DIR", "raw") # Uncomment if you want the html code of the individual pages to be saved
SAVE_HTML = os.getenv("SAVE_HTML", True)
CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "cna-rag")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral")
K_VALUE = os.getenv("K_SIMILAR", 10)
USE_EXISTING_DB = os.getenv("USE_EXISTING_DB", False)
METADATA = os.getenv("METADATA_FILE", "metadata.json")

reader = make_reader("db.sqlite")
html_parser = parse_html_to_txt_cna # CHANGE YOUR DESIRED PARSER (IMPLEMENT IT IN parse.py AND IMPORT IT FIRST)

def str_to_bool(value):
    if type(value) == bool: return value
    else: return value.lower() in ("true", "1", "yes")

# Reads a file and adds it to a dictionary
def readFiles(entries_dir):
    contents = []
    entries_dir = os.path.join(entries_dir)
    
    for filename in os.listdir(entries_dir):
        filePath = os.path.join(entries_dir, filename)
        if os.path.isdir(filePath):
            continue
        
        content = {}
        with open(filePath, "r", encoding="utf-8") as file:
            text = file.read()
            content["filename"] = filename
            content["text"] = text
            contents.append(content)

    return contents

# Splits a body of text into chunks for individual embedding
def chunkSplitter(text, chunk_size=100):
    words = re.findall(r"\S+", text)

    chunks = []
    chunk = []
    for i, w in enumerate(words):
        if i > 0 and i % chunk_size == 0:
            chunks.append(" ".join(chunk))
            chunk = []
        else:
            chunk.append(w)
    else:
        chunks.append(" ".join(chunk))

    return chunks

# Pull a model if it does not already exist
def pullModel(modelName):
    existingModels = [m.get("model").split(":")[0] for m in ollama.list().models]
    if not modelName in existingModels:
        print(f"Pulling model {modelName}.")
        ollama.pull(EMBED_MODEL)

# Check if Chroma db exists
def dbExists(name='chroma'):
    # Check for existing database
    if os.path.exists(os.path.join(CHROMA_PATH, name + '.sqlite3')):
        print(f'Existing db {name}.sqlite found.\n')
        return True
    else:
        print(f'No existing db {name}.sqlite found.\n')
        return False

# Initialize a Chroma client that will be used to access the collection
def getVectorDb(reset=False, name='chroma'):
    # Check for existing database
    chromaPath = os.path.join(CHROMA_PATH, name + '.sqlite3')

    if os.path.exists(chromaPath):
        print(f'Existing db {name}.sqlite found.')
        if reset:
            os.remove(chromaPath)
            print('Removing it.\n')
        else:
            print('Using it.\n')
    else:
        print(f'No existing db {name}.sqlite found.\n')

    db = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH,
        embedding_function=OllamaEmbeddings(model=EMBED_MODEL, show_progress=True),
    )

    return db

# Splits content into chunks and adds them into the db, embeding them in the process
def addToCollection(db, content):
    print("Embedding file {}".format(content["filename"]), end=' ')
    chunks = chunkSplitter(content["text"])
    ids = [str(i + 1) for i in range(len(chunks))]  # ids of all chunks
    metadatas = [ # Metadata of all chunks. Feel free to add more
        {"filename": content["filename"] + i} for i in ids
    ]  

    db.add_texts(chunks, metadatas, ids=ids)
    return

db = None
if __name__ == "__main__":
    k_value = int(K_VALUE)
    save_html = str_to_bool(SAVE_HTML)
    use_existing_db = str_to_bool(USE_EXISTING_DB)
    print('Use existing db:', use_existing_db)

    if not use_existing_db or not dbExists():

        # Update feed and obtain entries
        updateFeed(reader, RSS_URL)
        entries = getEntries(reader, RSS_URL)
        num_entries = len(entries)

        # Fetch entries and download them as text files
        os.makedirs(ENTRIES_DIR, exist_ok=True)
        entry_urls = [entry.link for entry in entries]
        downloaded = fetch_and_download(entry_urls, ENTRIES_DIR, METADATA, html_parser, html_dir=HTML_DIR if save_html else None)
        print("\nThe entries have been downloaded as text files.")

        # Embed text files
        cont = input("Proceed with embedding? (Yes / No) ")
        if cont.lower() == 'no': exit(0)
        contents = readFiles(ENTRIES_DIR)
        print("Now proceeding to embed files.\n")
        db = getVectorDb(reset=True)

        # Add each entry to collection (does chunking and embedding beforehand)
        total = len(contents)
        for i, content in enumerate(contents):
            addToCollection(db, content)
            print(f'{i+1} / {total} files embedded.')
            pass
        print('All files have been embedded.\n')

    
    if db is None:
        db = getVectorDb()
    context = [] # Used to store context

    # Begin querying loop
    while True:

        # Embed query and obtain related texts
        print()
        query = input("Enter your query: ")
        print('\nEmbedding query...')
        queryEmbed = ollama.embed(model=EMBED_MODEL, input=query)["embeddings"]
        relatedTexts = db.similarity_search(query=query, k=k_value) # Change k-value to retrieve more similar texts. Default is 4
        print("Obtained related texts.")

        # Pull LLM_MODEL if it does not already exist
        pullModel(LLM_MODEL)

        # EDIT SYSTEM PROMPT HOWEVER YOU DESIRE
        prompt = f"{query}\n\nAnswer the above query wih today's Channel News Asia (CNA) news, available as this resource: {relatedTexts}"

        # Generate response
        print("Generating response...\n")
        responseStream = ollama.generate(
            model=LLM_MODEL, prompt=prompt, stream=True, context=context
        )
        for chunk in responseStream:
            print(chunk.response, end='', flush=True)

        context += chunk.context