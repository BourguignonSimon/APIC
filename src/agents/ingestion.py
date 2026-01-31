"""
Node 1: Knowledge Ingestion Agent
Handles document parsing, chunking, and vector storage.
"""

import os
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from .base import BaseAgent, get_llm, get_embeddings
from src.models.schemas import Document, GraphState, ProjectStatus
from config.settings import settings


class IngestionAgent(BaseAgent):
    """
    Node 1: Knowledge Ingestion Agent

    Responsibilities:
    - Parse uploaded documents (PDF, DOCX, TXT, etc.)
    - Chunk documents for optimal retrieval
    - Generate embeddings and store in vector database
    - Create document summaries for context
    """

    def __init__(self, **kwargs):
        super().__init__(name="IngestionAgent", **kwargs)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        # Embeddings are lazy-loaded when needed to allow for missing API keys
        # during initialization (validation happens when actually used)
        self._embeddings = None

    @property
    def embeddings(self):
        """Lazy-load embeddings to defer API key validation until actually needed."""
        if self._embeddings is None:
            self._embeddings = get_embeddings()
        return self._embeddings

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process uploaded documents and store in vector database.

        Args:
            state: Current graph state with documents to process

        Returns:
            Updated state with ingestion results
        """
        try:
            project_id = state.get("project_id")
            documents = state.get("documents", [])

            if not documents:
                state["ingestion_complete"] = True
                state["messages"].append("No documents provided for ingestion")
                return state

            all_chunks = []
            document_summaries = []

            for doc in documents:
                if isinstance(doc, dict):
                    doc = Document(**doc)

                content = await self._parse_document(doc)

                if content:
                    chunks = self._chunk_document(content, doc)
                    all_chunks.extend(chunks)

                    summary = await self._generate_summary(content, doc.filename)
                    document_summaries.append(summary)

                    doc.chunk_count = len(chunks)
                    doc.processed = True
                    doc.content_summary = summary

            if all_chunks:
                try:
                    await self._store_in_vector_db(
                        chunks=all_chunks,
                        namespace=f"client_{project_id}",
                    )
                except Exception as vector_error:
                    self.log_error("Vector storage failed", vector_error)
                    state["messages"].append(
                        "Warning: Vector storage unavailable. Semantic search may be limited."
                    )

            state["documents"] = [
                d.model_dump() if hasattr(d, 'model_dump') else d
                for d in documents
            ]
            state["document_summaries"] = document_summaries
            state["ingestion_complete"] = True
            state["current_node"] = "ingestion"
            state["messages"].append(
                f"Processed {len(documents)} documents into {len(all_chunks)} chunks"
            )

            return state

        except Exception as e:
            self.log_error("Ingestion failed", e)
            state["errors"].append(f"Ingestion error: {str(e)}")
            state["ingestion_complete"] = False
            return state

    async def _parse_document(self, doc: Document) -> Optional[str]:
        """
        Parse document content based on file type.

        Args:
            doc: Document model with file information

        Returns:
            Extracted text content
        """
        file_path = os.path.join(settings.UPLOAD_DIR, doc.project_id, doc.filename)

        if not os.path.exists(file_path):
            return None

        file_type = doc.file_type.lower()

        try:
            if file_type == "pdf":
                return await self._parse_pdf(file_path)
            elif file_type in ["docx", "doc"]:
                return await self._parse_docx(file_path)
            elif file_type == "txt":
                return await self._parse_txt(file_path)
            elif file_type == "pptx":
                return await self._parse_pptx(file_path)
            else:
                return await self._parse_txt(file_path)
        except Exception as e:
            self.log_error(f"Error parsing {doc.filename}", e)
            return None

    async def _parse_pdf(self, file_path: str) -> str:
        """Parse PDF document."""
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()

    async def _parse_docx(self, file_path: str) -> str:
        """Parse DOCX document."""
        from docx import Document as DocxDocument

        doc = DocxDocument(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()

    async def _parse_txt(self, file_path: str) -> str:
        """Parse plain text document."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()

    async def _parse_pptx(self, file_path: str) -> str:
        """Parse PowerPoint document."""
        from pptx import Presentation

        prs = Presentation(file_path)
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return "\n".join(text).strip()

    def _chunk_document(
        self,
        content: str,
        doc: Document,
    ) -> List[LCDocument]:
        """
        Chunk document content for vector storage.

        Args:
            content: Raw text content
            doc: Document metadata

        Returns:
            List of LangChain Document objects
        """
        chunks = self.text_splitter.split_text(content)

        return [
            LCDocument(
                page_content=chunk,
                metadata={
                    "document_id": doc.id,
                    "project_id": doc.project_id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "chunk_index": i,
                    "chunk_hash": hashlib.md5(chunk.encode()).hexdigest(),
                },
            )
            for i, chunk in enumerate(chunks)
        ]

    async def _generate_summary(self, content: str, filename: str) -> str:
        """
        Generate a summary of the document content.

        Args:
            content: Full document text
            filename: Name of the file

        Returns:
            Summary text
        """
        # Truncate content if too long
        max_content_length = 10000
        truncated_content = content[:max_content_length]
        if len(content) > max_content_length:
            truncated_content += "... [truncated]"

        # Get configurable prompt or use default
        default_prompt = """Analyze the following document and provide a concise summary
        that captures the main topics, processes, and any potential areas
        of operational inefficiency or improvement.

        Document: {filename}

        Content:
        {content}

        Provide a summary in 2-3 paragraphs focusing on:
        1. Main purpose and content of the document
        2. Key processes or procedures described
        3. Any notable patterns, pain points, or areas that might benefit from automation
        """

        prompt_template = self.get_prompt("summary", default_prompt)
        prompt = prompt_template.format(filename=filename, content=truncated_content)

        response = await self.llm.ainvoke(prompt)
        return response.content

    async def _get_or_generate_summary(
        self,
        document_id: str,
        content: str,
        filename: str = "document"
    ) -> str:
        """
        Get cached summary or generate a new one.

        Args:
            document_id: Unique document identifier
            content: Document content
            filename: Name of the file

        Returns:
            Document summary
        """
        from src.services.llm_cache import get_llm_cache

        cache = get_llm_cache()
        cache_key = f"summary_{document_id}"

        cached_summary = await cache.get(cache_key)
        if cached_summary:
            return cached_summary

        summary = await self._generate_summary(content, filename)
        await cache.set(cache_key, summary)

        return summary

    async def _store_in_vector_db(
        self,
        chunks: List[LCDocument],
        namespace: str,
    ) -> None:
        """
        Store document chunks in Pinecone vector database.

        Args:
            chunks: List of document chunks
            namespace: Vector DB namespace for isolation
        """
        if not settings.PINECONE_API_KEY:
            return

        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index_name = settings.PINECONE_INDEX_NAME
        existing_indexes = [idx.name for idx in pc.list_indexes()]

        if index_name not in existing_indexes:
            pc.create_index(
                name=index_name,
                dimension=1536,
                metric="cosine",
                spec={
                    "serverless": {
                        "cloud": "aws",
                        "region": settings.PINECONE_ENVIRONMENT,
                    }
                },
            )

        PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            index_name=index_name,
            namespace=namespace,
        )

    async def query_knowledge_base(
        self,
        query: str,
        namespace: str,
        top_k: int = 5,
    ) -> List[LCDocument]:
        """
        Query the vector database for relevant documents.

        Args:
            query: Search query
            namespace: Vector DB namespace
            top_k: Number of results to return

        Returns:
            List of relevant document chunks
        """
        if not settings.PINECONE_API_KEY:
            return []

        try:
            vector_store = PineconeVectorStore(
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=self.embeddings,
                namespace=namespace,
            )
            return vector_store.similarity_search(query, k=top_k)
        except Exception:
            return []
