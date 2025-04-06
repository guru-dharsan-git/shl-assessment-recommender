from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import pandas as pd
import numpy as np

# Create embeddings
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db_location = "./chrome_shl_db"
add_documents = not os.path.exists(db_location)

# Function to create a more comprehensive document text
def create_assessment_text(row):
    # Create a detailed text representation with all information
    return f"""
    Name: {row['Name']}
    Type: {row['Type']}
    Skills: {row['Skills']}
    Description: {row['Description']}
    Duration: {row['Duration']}
    Remote Testing: {row['RemoteTesting']}
    Adaptive/IRT Support: {row['AdaptiveSupport']}
    URL: {row['URL']}
    
    This assessment evaluates {row['Skills']} skills and is a {row['Type']} assessment type.
    It takes {row['Duration']} to complete and {'' if row['RemoteTesting'] == 'Yes' else 'does not '}
    support remote testing. It {'' if row['AdaptiveSupport'] == 'Yes' else 'does not '} have adaptive/IRT support.
    
    {row['Description']}
    """

if add_documents:
    try:
        # Load SHL assessment data
        df = pd.read_csv("shl_assessments_with_skills.csv")
        documents = []
        ids = []
        
        for i, row in df.iterrows():
            # Create document with comprehensive assessment details
            assessment_text = create_assessment_text(row)
            
            document = Document(
                page_content=assessment_text,
                metadata={
                    "name": row["Name"],
                    "type": row["Type"],
                    "skills": row["Skills"],
                    "description": row["Description"],
                    "duration": row["Duration"],
                    "remote_testing": row["RemoteTesting"],
                    "adaptive_support": row["AdaptiveSupport"],
                    "url": row["URL"]
                },
                id=str(i)
            )
            ids.append(str(i))
            documents.append(document)
            
        print(f"Creating vector store with {len(documents)} documents")
        vector_store = Chroma(
            collection_name="shl_assessments",
            persist_directory=db_location,
            embedding_function=embeddings
        )
        
        # Add documents in batches to avoid memory issues
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            end = min(i + batch_size, len(documents))
            vector_store.add_documents(documents=documents[i:end], ids=ids[i:end])
            print(f"Added documents {i} to {end-1}")
        
        # Persist after adding all documents
        vector_store.persist()
        print("Vector store created and persisted successfully")
    except Exception as e:
        print(f"Error creating vector store: {e}")
        # Create an empty directory to prevent repeated attempts
        if not os.path.exists(db_location):
            os.makedirs(db_location)
else:
    print("Using existing vector store")
    # Load the existing vector store
    vector_store = Chroma(
        collection_name="shl_assessments",
        persist_directory=db_location,
        embedding_function=embeddings
    )

# Custom retriever with fallback
class SHLRetriever:
    def __init__(self, vector_store, k=10):
        self.vector_store = vector_store
        self.k = k
        # Load full dataset for fallback
        try:
            self.df = pd.read_csv("shl_assessments_with_skills.csv")
        except:
            self.df = None

    def invoke(self, query):
        # First try vector store retrieval
        try:
            docs = self.vector_store.as_retriever(search_kwargs={"k": self.k}).invoke(query)
            if docs and len(docs) > 0:
                return docs
        except Exception as e:
            print(f"Vector retrieval error: {e}")
        
        # Fallback: return random documents if vector retrieval fails or returns empty
        if self.df is not None:
            print("Using fallback retrieval")
            sample_indices = np.random.choice(len(self.df), min(self.k, len(self.df)), replace=False)
            documents = []
            
            for idx in sample_indices:
                row = self.df.iloc[idx]
                assessment_text = create_assessment_text(row)
                
                document = Document(
                    page_content=assessment_text,
                    metadata={
                        "name": row["Name"],
                        "type": row["Type"],
                        "skills": row["Skills"],
                        "description": row["Description"],
                        "duration": row["Duration"],
                        "remote_testing": row["RemoteTesting"],
                        "adaptive_support": row["AdaptiveSupport"],
                        "url": row["URL"]
                    },
                    id=str(idx)
                )
                documents.append(document)
            
            return documents
        
        # Last resort: return an empty list
        return []

# Create the retriever instance
retriever = SHLRetriever(vector_store)