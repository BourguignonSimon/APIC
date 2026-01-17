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
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from .base import BaseAgent, get_llm
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
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small",
        )

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process uploaded documents and store in vector database.

        Args:
            state: Current graph state with documents to process

        Returns:
            Updated state with ingestion results
        """
        self.log_info("Starting document ingestion process")

        try:
            project_id = state.get("project_id")
            documents = state.get("documents", [])

            if not documents:
                self.log_info("No documents to process")
                state["ingestion_complete"] = True
                state["messages"].append("No documents provided for ingestion")
                return state

            # Process each document
            all_chunks = []
            document_summaries = []

            for doc in documents:
                if isinstance(doc, dict):
                    doc = Document(**doc)

                self.log_info(f"Processing document: {doc.filename}")

                # Parse document based on type
                content = await self._parse_document(doc)

                if content:
                    # Chunk the content
                    chunks = self._chunk_document(content, doc)
                    all_chunks.extend(chunks)

                    # Generate summary
                    summary = await self._generate_summary(content, doc.filename)
                    document_summaries.append(summary)

                    # Update document metadata
                    doc.chunk_count = len(chunks)
                    doc.processed = True
                    doc.content_summary = summary

            # Store chunks in vector database
            if all_chunks:
                await self._store_in_vector_db(
                    chunks=all_chunks,
                    namespace=f"client_{project_id}",
                )
                self.log_info(f"Stored {len(all_chunks)} chunks in vector database")

            # Update state
            state["documents"] = [
                d.model_dump() if hasattr(d, 'model_dump') else d
                for d in documents
            ]
            state["document_summaries"] = document_summaries
            state["ingestion_complete"] = True
            state["current_node"] = "ingestion"
            state["messages"].append(
                f"Successfully processed {len(documents)} documents "
                f"into {len(all_chunks)} chunks"
            )

            self.log_info("Document ingestion complete")
            return state

        except Exception as e:
            self.log_error("Error during ingestion", e)
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
            self.log_error(f"File not found: {file_path}")
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
                self.log_info(f"Unsupported file type: {file_type}, attempting text extraction")
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

        prompt = f"""Analyze the following document and provide a concise summary
        that captures the main topics, processes, and any potential areas
        of operational inefficiency or improvement.

        Document: {filename}

        Content:
        {truncated_content}

        Provide a summary in 2-3 paragraphs focusing on:
        1. Main purpose and content of the document
        2. Key processes or procedures described
        3. Any notable patterns, pain points, or areas that might benefit from automation
        """

        response = await self.llm.ainvoke(prompt)
        return response.content

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
            self.log_info("Pinecone API key not configured, skipping vector storage")
            return

        try:
            # Initialize Pinecone
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)

            # Get or create index
            index_name = settings.PINECONE_INDEX_NAME

            # Check if index exists
            existing_indexes = [idx.name for idx in pc.list_indexes()]

            if index_name not in existing_indexes:
                self.log_info(f"Creating Pinecone index: {index_name}")
                pc.create_index(
                    name=index_name,
                    dimension=1536,  # text-embedding-3-small dimension
                    metric="cosine",
                    spec={
                        "serverless": {
                            "cloud": "aws",
                            "region": settings.PINECONE_ENVIRONMENT,
                        }
                    },
                )

            # Store vectors
            vector_store = PineconeVectorStore.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                index_name=index_name,
                namespace=namespace,
            )

            self.log_info(f"Successfully stored {len(chunks)} vectors in namespace: {namespace}")

        except Exception as e:
            self.log_error("Error storing vectors in Pinecone", e)
            raise

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
            self.log_info("Pinecone API key not configured")
            return []

        try:
            vector_store = PineconeVectorStore(
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=self.embeddings,
                namespace=namespace,
            )

            results = vector_store.similarity_search(query, k=top_k)
            return results

        except Exception as e:
            self.log_error("Error querying vector database", e)
            return []
