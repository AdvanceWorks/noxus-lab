#!/usr/bin/env python3
"""Create a Knowledge Base, ingest a document, search it.

    python examples/03_kb.py [path/to/doc.txt]

Steps:
    1. Create a v3 KB with an explicit embedding model.
    2. Upload one document (a small inline sample if none is given).
    3. Poll until the document is trained.
    4. Run a vector search and print the top hit.

We stop at `kb.search`. Wiring a chat agent on top of the KB needs a
workspace with a reranker and QA model enabled, which is out of scope
for this lab.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.resources.knowledge_bases import KBConfigV3

SAMPLE = (
    "Acme Robotics is a fictional company that builds warehouse "
    "automation solutions. Its flagship product, the AcmeBot 9000, "
    "can lift up to 50 kg and runs on rechargeable batteries."
)

load_dotenv()
c = Client(
    api_key=os.environ["NOXUS_API_KEY"],
    base_url=os.environ.get("NOXUS_BACKEND_URL"),
)

if len(sys.argv) > 1:
    doc = sys.argv[1]
else:
    doc = str(Path(tempfile.mkdtemp()) / "sample.txt")
    Path(doc).write_text(SAMPLE, encoding="utf-8")

kb = c.knowledge_bases.create(
    name="noxus-lab-sample",
    description="Sample KB created by examples/03_kb.py",
    document_types=["txt", "pdf"],
    settings_=KBConfigV3(
        embedding_model=["vertexai/text-multilingual-embedding-002"],
        default_chunk_size=600,
        default_chunk_overlap=100,
    ),
    version="v3",
)
print("kb:", kb.id)

kb.upload_document(files=[doc], prefix="/")
for _ in range(60):
    kb.refresh()
    if kb.trained_documents > 0:
        break
    time.sleep(2)
print(f"trained: {kb.trained_documents}/{kb.total_documents}")

# The backend index needs a moment to warm up after training.
time.sleep(15)

query = "What is GBE-PAS?"
hits = kb.search(query=query)
print(f"query: {query}")
if not hits:
    print("no hits")
else:
    top = hits[0]
    print(f"score: {top.score:.2f}")
    print(top.content)
