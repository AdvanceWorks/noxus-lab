#!/usr/bin/env python3
"""Run several KB operations in parallel using the SDK's async API.

    python examples/05_async.py

Creates 3 small KBs concurrently with `asyncio.gather`, then deletes
them. Demonstrates the `aXxx` method naming convention and how to drive
the SDK from an event loop.
"""

import asyncio
import os

from dotenv import load_dotenv
from noxus_sdk.client import Client
from noxus_sdk.resources.knowledge_bases import KBConfigV3

load_dotenv()
c = Client(
    api_key=os.environ["NOXUS_API_KEY"],
    base_url=os.environ.get("NOXUS_BACKEND_URL"),
)


async def make(i):
    kb = await c.knowledge_bases.acreate(
        name=f"noxus-lab-async-{i}",
        description="ephemeral",
        document_types=["txt"],
        settings_=KBConfigV3(
            embedding_model=["vertexai/text-multilingual-embedding-002"],
            default_chunk_size=600,
            default_chunk_overlap=100,
        ),
        version="v3",
    )
    print("created:", kb.id)
    return kb


async def go():
    kbs = await asyncio.gather(*(make(i) for i in range(3)))
    await asyncio.gather(*(kb.adelete() for kb in kbs))
    print(f"deleted {len(kbs)} KBs")


asyncio.run(go())
