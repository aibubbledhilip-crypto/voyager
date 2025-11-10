"""
RAG Engine for intelligent data analysis
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

from backend.config import settings
from backend.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG Engine for data analysis using LangChain and ChromaDB"""

    def __init__(self):
        self.data_processor = DataProcessor()
        self.vectorstore = None
        self.embeddings = None
        self.llm = None
        self.qa_chain = None

        self._initialize_embeddings()
        self._initialize_llm()
        self._initialize_vectorstore()

    def _initialize_embeddings(self):
        """Initialize embedding model"""
        try:
            if settings.embedding_provider == "openai":
                if not settings.openai_api_key:
                    raise ValueError("OpenAI API key not provided")

                # Use model without the version suffix to avoid tiktoken warning
                model_name = settings.embedding_model
                if model_name == "text-embedding-3-small":
                    # tiktoken doesn't recognize this model yet, but it works fine
                    import warnings
                    warnings.filterwarnings('ignore', message='.*model not found.*')

                self.embeddings = OpenAIEmbeddings(
                    model=model_name,
                    openai_api_key=settings.openai_api_key
                )
                logger.info(f"Initialized OpenAI embeddings: {model_name}")
            else:
                # Use local sentence-transformers
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=settings.embedding_model or "all-MiniLM-L6-v2"
                )
                logger.info(f"Initialized local embeddings: {settings.embedding_model}")
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise

    def _initialize_llm(self):
        """Initialize LLM"""
        try:
            if settings.llm_provider == "openai":
                if not settings.openai_api_key:
                    raise ValueError("OpenAI API key not provided")
                self.llm = ChatOpenAI(
                    model=settings.llm_model,
                    temperature=0,
                    openai_api_key=settings.openai_api_key
                )
                logger.info(f"Initialized OpenAI LLM: {settings.llm_model}")
            else:
                # For Anthropic, we'll use a custom approach
                from langchain_community.chat_models import ChatAnthropic
                if not settings.anthropic_api_key:
                    raise ValueError("Anthropic API key not provided")
                self.llm = ChatAnthropic(
                    model=settings.llm_model,
                    anthropic_api_key=settings.anthropic_api_key
                )
                logger.info(f"Initialized Anthropic LLM: {settings.llm_model}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise

    def _initialize_vectorstore(self):
        """Initialize or load ChromaDB vectorstore"""
        try:
            persist_dir = Path(settings.chroma_persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)

            self.vectorstore = Chroma(
                persist_directory=str(persist_dir),
                embedding_function=self.embeddings,
                collection_name="data_analysis"
            )
            logger.info(f"Initialized ChromaDB at {persist_dir}")

            # Initialize QA chain
            self._initialize_qa_chain()
        except Exception as e:
            logger.error(f"Error initializing vectorstore: {str(e)}")
            raise

    def _initialize_qa_chain(self):
        """Initialize the QA chain with custom prompt"""
        template = """You are an intelligent data analysis assistant. Use the following context from the datasets to answer the question.

The context contains data from multiple Excel/CSV files. Each piece of context includes:
- Dataset summaries with column names, data types, and statistics
- Actual data rows from the files
- Metadata about the source files

When answering:
1. Provide specific insights based on the data
2. Reference which dataset(s) you're using
3. Include relevant statistics, trends, or patterns
4. If asked for numerical analysis, provide precise calculations
5. If the context doesn't contain enough information, say so clearly

Context from the datasets:
{context}

Question: {question}

Detailed Answer:"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 20}  # Retrieve top 20 chunks (balanced for token limits and file coverage)
            ),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        logger.info("Initialized QA chain")

    def add_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process and add a file to the vectorstore
        """
        file_name = Path(file_path).name

        try:
            if not self.data_processor.is_supported_file(file_path):
                return {
                    "success": False,
                    "file_name": file_name,
                    "error": "Unsupported file format"
                }

            # Read the file
            df = self.data_processor.read_file(file_path)
            if df is None:
                return {
                    "success": False,
                    "file_name": file_name,
                    "error": "Failed to read file"
                }

            # Chunk the data
            chunks = self.data_processor.chunk_dataframe(df, file_name)

            # Convert to LangChain documents
            documents = [
                Document(
                    page_content=chunk["content"],
                    metadata=chunk["metadata"]
                )
                for chunk in chunks
            ]

            # Add to vectorstore
            self.vectorstore.add_documents(documents)
            self.vectorstore.persist()

            # Extract insights
            insights = self.data_processor.extract_insights(df)

            logger.info(f"Successfully added {file_name} to vectorstore with {len(documents)} chunks")

            return {
                "success": True,
                "file_name": file_name,
                "chunks_created": len(documents),
                "insights": insights
            }

        except Exception as e:
            logger.error(f"Error adding file {file_path}: {str(e)}")
            return {
                "success": False,
                "file_name": file_name,
                "error": str(e)
            }

    def add_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Add multiple files to the vectorstore"""
        results = []
        for file_path in file_paths:
            result = self.add_file(file_path)
            results.append(result)
        return results

    def query(self, question: str, return_sources: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system
        """
        try:
            if not self.qa_chain:
                return {
                    "success": False,
                    "error": "QA chain not initialized"
                }

            # Run the query
            result = self.qa_chain({"query": question})

            response = {
                "success": True,
                "question": question,
                "answer": result["result"]
            }

            if return_sources and "source_documents" in result:
                sources = []
                for doc in result["source_documents"]:
                    sources.append({
                        "content": doc.page_content[:500],  # First 500 chars
                        "metadata": doc.metadata
                    })
                response["sources"] = sources

            logger.info(f"Successfully answered query: {question[:100]}")
            return response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_data_overview(self) -> Dict[str, Any]:
        """Get an overview of all data in the vectorstore"""
        try:
            # Query for all unique files
            all_docs = self.vectorstore.get()

            if not all_docs or 'metadatas' not in all_docs:
                return {
                    "total_files": 0,
                    "total_chunks": 0,
                    "files": []
                }

            # Extract unique files and their info
            files_info = {}
            for metadata in all_docs['metadatas']:
                if metadata and 'file_name' in metadata:
                    file_name = metadata['file_name']
                    if file_name not in files_info:
                        files_info[file_name] = {
                            "file_name": file_name,
                            "total_rows": metadata.get('total_rows', 0),
                            "columns": metadata.get('columns', []),
                            "chunks": 0
                        }
                    files_info[file_name]["chunks"] += 1

            return {
                "total_files": len(files_info),
                "total_chunks": len(all_docs['metadatas']),
                "files": list(files_info.values())
            }

        except Exception as e:
            logger.error(f"Error getting data overview: {str(e)}")
            return {
                "error": str(e)
            }

    def clear_vectorstore(self):
        """Clear all data from the vectorstore"""
        try:
            # Delete the collection and recreate
            self.vectorstore.delete_collection()
            self._initialize_vectorstore()
            logger.info("Cleared vectorstore")
            return {"success": True, "message": "Vectorstore cleared"}
        except Exception as e:
            logger.error(f"Error clearing vectorstore: {str(e)}")
            return {"success": False, "error": str(e)}
