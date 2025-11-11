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
                    temperature=settings.llm_temperature,  # Configurable temperature
                    openai_api_key=settings.openai_api_key
                )
                logger.info(f"Initialized OpenAI LLM: {settings.llm_model} (temperature={settings.llm_temperature})")
            else:
                # For Anthropic, we'll use a custom approach
                from langchain_community.chat_models import ChatAnthropic
                if not settings.anthropic_api_key:
                    raise ValueError("Anthropic API key not provided")
                self.llm = ChatAnthropic(
                    model=settings.llm_model,
                    temperature=settings.llm_temperature,  # Configurable temperature
                    anthropic_api_key=settings.anthropic_api_key
                )
                logger.info(f"Initialized Anthropic LLM: {settings.llm_model} (temperature={settings.llm_temperature})")
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
        """Initialize the QA chain with anti-hallucination prompt"""
        template = """You are a precise data analysis assistant. Your role is to provide accurate answers based ONLY on the provided context.

CRITICAL RULES TO PREVENT HALLUCINATION:
1. ONLY use information explicitly present in the context below
2. DO NOT make assumptions or extrapolate beyond the given data
3. DO NOT use external knowledge or general information
4. If the context lacks sufficient information to answer, clearly state: "The provided data does not contain enough information to answer this question."
5. ALWAYS cite which specific file(s) you're referencing
6. For numerical questions, ONLY provide numbers that appear in the context
7. If asked about data not present in the context, say: "I don't have data about [topic] in the uploaded files."

The context contains data from multiple Excel/CSV files:
- Dataset summaries with column names, data types, and statistics
- Actual data rows from the files
- Metadata about the source files

Context from the datasets:
{context}

Question: {question}

Instructions for your answer:
1. Start by identifying which file(s) contain relevant information
2. Provide specific insights based ONLY on the data shown above
3. Include relevant statistics, but ONLY those present in the context
4. If asked for counts/aggregations you cannot verify from the context, suggest using the analytics endpoints instead
5. If uncertain or data is incomplete, explicitly state the limitation

Answer:"""

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
        logger.info("Initialized QA chain with anti-hallucination prompt")

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

    def _validate_answer(self, answer: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate answer for potential hallucination markers
        Returns: {is_valid: bool, warnings: List[str], confidence: str}
        """
        warnings = []

        # Hallucination markers (phrases that suggest made-up information)
        hallucination_markers = [
            "i think", "probably", "might be", "could be", "perhaps",
            "in general", "typically", "usually", "commonly",
            "based on my knowledge", "as far as i know"
        ]

        answer_lower = answer.lower()

        # Check for hallucination markers
        for marker in hallucination_markers:
            if marker in answer_lower:
                warnings.append(f"Uncertain language detected: '{marker}'")

        # Check if answer mentions file names from sources
        if sources and settings.require_source_citation:
            source_files = set()
            for source in sources:
                if 'metadata' in source and 'file_name' in source['metadata']:
                    source_files.add(source['metadata']['file_name'])

            # Check if at least one source file is mentioned in the answer
            files_mentioned = any(file_name in answer for file_name in source_files)
            if not files_mentioned and source_files:
                warnings.append("Answer does not cite specific source files")

        # Check for "I don't have" or "not enough information" (good - means honest about limitations)
        honesty_markers = [
            "don't have", "not enough information", "cannot determine",
            "insufficient data", "not present in", "does not contain"
        ]
        is_honest = any(marker in answer_lower for marker in honesty_markers)

        # Determine confidence
        if len(warnings) == 0:
            confidence = "high"
        elif len(warnings) <= 2:
            confidence = "medium"
        else:
            confidence = "low"

        # If answer is honestly stating limitations, that's actually good
        if is_honest:
            confidence = "high"  # Honesty about limitations is good
            warnings = [w for w in warnings if "uncertain language" not in w.lower()]

        return {
            "is_valid": len(warnings) <= 2,  # Allow up to 2 minor warnings
            "warnings": warnings,
            "confidence": confidence,
            "is_honest_about_limitations": is_honest
        }

    def query(self, question: str, return_sources: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system with anti-hallucination validation
        """
        try:
            if not self.qa_chain:
                return {
                    "success": False,
                    "error": "QA chain not initialized"
                }

            # Run the query
            result = self.qa_chain({"query": question})

            answer = result["result"]
            sources = []

            if "source_documents" in result:
                for doc in result["source_documents"]:
                    sources.append({
                        "content": doc.page_content[:500],  # First 500 chars
                        "metadata": doc.metadata
                    })

            # Validate answer for hallucination markers
            validation = None
            if settings.enable_answer_validation:
                validation = self._validate_answer(answer, sources)
                logger.info(f"Answer validation: confidence={validation['confidence']}, warnings={len(validation['warnings'])}")

                # Add warning to answer if confidence is low
                if validation['confidence'] == 'low' and validation['warnings']:
                    warning_note = "\n\n⚠️ **Note**: This answer may be uncertain. Validation warnings:\n"
                    for warning in validation['warnings']:
                        warning_note += f"- {warning}\n"
                    warning_note += "\nConsider using analytics endpoints for exact data queries."
                    answer += warning_note

            response = {
                "success": True,
                "question": question,
                "answer": answer
            }

            if return_sources:
                response["sources"] = sources

            # Add validation metadata if enabled
            if validation and settings.enable_answer_validation:
                response["validation"] = {
                    "confidence": validation["confidence"],
                    "warnings": validation["warnings"],
                    "is_valid": validation["is_valid"]
                }

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
                    "success": True,
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
                "success": True,
                "total_files": len(files_info),
                "total_chunks": len(all_docs['metadatas']),
                "files": list(files_info.values())
            }

        except Exception as e:
            logger.error(f"Error getting data overview: {str(e)}")
            return {
                "success": False,
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
