# CNA-RSS-RAG
This is a simple Python program that performs RAG on the Channel News Asia RSS feed. It does so locally, using Ollama.

# How RAG works

1. Break the file into chunks.
2. Embed each chunk in a vector database (Chroma) using a text embedding model (Nomic by default).
3. Ask a query.
4. Map the query to an embedding.
5. Obtain the top K embeddings most similar to the query embedding.
6. Pass the query embedding + the K most similar embeddings into the LLM (Mistral by default).
7. Model will generate a response.

# Running the script
1. Make sure you have python>=3.6 installed. Then install the required dependencies:
```python
pip install -r requirements.txt
```

2. Run main.py
```python
python main.py
```

3. After the program finishes embedding all chunks, you may begin asking queries.

# Environment variables (.env file)
**RSS_URL** - 
Set to CNA's RSS feed URL by default. Feel free to change to a different RSS feed, but you'll need to write your own HTML parser in parse.py.

**ENTRIES_DIR** - 
The name of the directory where downloaded and processed RSS entries will be stored in txt files.

**HTML_DIR** - 
Name of directory to which the raw HTML of individual entries are downloaded.

**SAVE_HTML** - 
Boolean value which specifies whether or not to save the raw HTML of entries to HTML_DIR.

**USE_EXISTING_DB** - 
If set to True, the program will skip the downloading and embedding phase and go straight into the querying phase, using an existing chroma.sqlite file in CHROMA_PATH.

**CHROMA_PATH** - 
The name of the directory that will store the local Chroma db, chroma.sqlite.

**COLLECTION_NAME** - 
The name of the Chroma db collection. Change as you please.

**LLM_MODEL** - 
Name of text generation model to use. Go to the [Ollama library](https://ollama.com/library) to view all available open-source LLMs.

**EMBED_MODEL** - 
Name of text embedding model to use, also from the [Ollama library](https://ollama.com/library).

**K_SIMILAR** - 
The top *k* most relevant chunks related to the query will be retrieved and passed into the model. If the model's response is too constrained to only a few news articles, increase this value.

**METADATA_FILE** - 
Stores the names of downloaded entries and their download dates in json format.

# Adding custom parsers
You can adapt this program to your own chosen RSS feed by firstly, changing the RSS_URL environment variable in the .env file and secondly, writing a parser to extract out the relevant content from individual RSS entries. Add your parser under parser.py. Check out [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/#navigating-the-tree).
