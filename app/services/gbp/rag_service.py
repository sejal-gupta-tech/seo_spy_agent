import chromadb
from chromadb.config import Settings
from app.core.openai_client import get_openai_client
import uuid
from typing import Dict, Any, List
import json

# Attempt to connect to a ChromaDB server
try:
    chroma_client = chromadb.HttpClient(host="localhost", port=8000)
except Exception as e:
    print(f"Warning: Could not connect to ChromaDB server: {e}")
    chroma_client = None

def get_or_create_collection():
    if not chroma_client:
        return None
    try:
        return chroma_client.get_or_create_collection(name="seo_spy_gbp_rag")
    except Exception:
        return None

async def index_document(user_id: str, location_id: str, doc_type: str, content: str, meta: Dict[str, Any] = None):
    """
    Indexes a document into ChromaDB for RAG.
    """
    collection = get_or_create_collection()
    if not collection:
        return False
        
    client = get_openai_client()
    if not client:
        return False
        
    try:
        # Get embedding
        resp = client.embeddings.create(
            input=content,
            model="text-embedding-3-small"
        )
        embedding = resp.data[0].embedding
        
        metadata = {
            "user_id": user_id,
            "location_id": location_id,
            "document_type": doc_type,
            "created_at": str(meta.get("created_at", "")) if meta else ""
        }
        
        doc_id = f"{doc_type}_{uuid.uuid4().hex[:12]}"
        
        collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return True
    except Exception as e:
        print(f"Error indexing to Chroma: {e}")
        return False

async def ask_rag_question(user_id: str, location_id: str, question: str) -> Dict[str, Any]:
    """
    Answers a question based on retrieved local SEO context from ChromaDB.
    """
    collection = get_or_create_collection()
    openai_client = get_openai_client()
    
    if not collection or not openai_client:
        return {
            "answer": "RAG Service is currently unavailable (ChromaDB or OpenAI not configured).",
            "evidence": []
        }
        
    try:
        # Embed question
        resp = openai_client.embeddings.create(
            input=question,
            model="text-embedding-3-small"
        )
        q_embedding = resp.data[0].embedding
        
        # Query Chroma, filtering strictly by user_id and location_id for tenant isolation
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=5,
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"location_id": {"$eq": location_id}}
                ]
            }
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        
        if not documents:
            return {
                "answer": "I don't have enough data in your local SEO records to answer that.",
                "evidence": []
            }
            
        # Build Context
        context_text = "\n\n".join([f"Evidence {i+1}: {doc}" for i, doc in enumerate(documents)])
        
        prompt = f"""
        You are an AI Local SEO Assistant. Answer the user's question based strictly on the provided Evidence.
        Do not answer from unrelated data. If the evidence doesn't contain the answer, say so.
        
        Evidence:
        {context_text}
        
        Question: {question}
        """
        
        chat_resp = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful SEO assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        answer = chat_resp.choices[0].message.content.strip()
        
        evidence_list = []
        for idx, (doc, meta, doc_id) in enumerate(zip(documents, metadatas, ids)):
            evidence_list.append({
                "record_id": doc_id,
                "document_type": meta.get("document_type", "unknown"),
                "snippet": doc[:150] + "..." if len(doc) > 150 else doc
            })
            
        return {
            "answer": answer,
            "evidence": evidence_list
        }
        
    except Exception as e:
        print(f"Error querying RAG: {e}")
        return {
            "answer": f"Error performing RAG query: {str(e)}",
            "evidence": []
        }
