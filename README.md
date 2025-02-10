# CNA-RSS-RAG
A simple Python program that performs RAG on the Channel News Asia RSS feed. It does so locally, using Ollama.

# Running the script
1. Make sure you have python>=3.6 installed. Then install the required dependencies:
```python
pip install -r requirements.txt
```

2. Run main.py
```python
python main.py
```

3. After the program finishes embedding all chunks, you may begin asking queries

# Environment variables (.env file)
**RSS_URL**
Set to CNA's RSS feed URL by default. Feel free to change to a different RSS feed, but you'll need to write your own HTML parser in parse.py.

**ENTRIES_DIR**
The name of the directory where downloaded and processed RSS entries will be stored in txt files.

**HTML_DIR**
Name of directory to which the raw HTML of individual entries are downloaded.

**SAVE_HTML**
Boolean value which specifies whether or not to save the raw HTML of entries to HTML_DIR.

**USE_EXISTING_DB**
If set to True, the program will skip the downloading and embedding phase and go straight into the querying phase, using an existing chroma.sqlite file in CHROMA_PATH.

**CHROMA_PATH**
The name of the directory which will store the local Chroma db, chroma.sqlite.

**COLLECTION_NAME**
The name of the Chroma db collection. Change as you please.

**LLM_MODEL**
Name of text generation model to use. Go to the [Ollama library](https://ollama.com/library) to view all available open-source LLMs.

**EMBED_MODEL**
Name of text embedding model to use, also from the [Ollama library](https://ollama.com/library).

**K_SIMILAR**  
The top *k* most relevant chunks related to the query will be retrieved and passed into the model. If the model's response is too constrained to only a few news articles, increase this value.

**METADATA_FILE**
Stores the names of downloaded entries and their date of download in json format.
