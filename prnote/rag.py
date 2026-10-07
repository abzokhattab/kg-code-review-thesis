"""RAG (Retrieval-Augmented Generation) module.

Builds and queries a semantic index of repository code for
finding similar code patterns and related implementations.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib


# =============================================================================
# CONFIGURATION
# =============================================================================

# File extensions to index
INDEXABLE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs',
    '.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.php', '.scala',
    '.kt', '.swift', '.m', '.sh'
}

# Directories to skip
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', 'env',
    '.venv', 'vendor', 'dist', 'build', '.next', '.nuxt',
    'target', 'out', 'coverage', '.pytest_cache'
}

# Chunk settings
CHUNK_SIZE = 500  # tokens (approximate)
CHUNK_OVERLAP = 50


# =============================================================================
# CHUNKING
# =============================================================================

def chunk_file(file_path: str, content: str, chunk_size: int = CHUNK_SIZE) -> List[Dict[str, Any]]:
    """
    Split file content into overlapping chunks for embedding.
    
    Args:
        file_path: Path to the file
        content: File content
        chunk_size: Approximate tokens per chunk
    
    Returns:
        List of chunk dictionaries with metadata
    """
    lines = content.split('\n')
    chunks = []
    
    # Simple line-based chunking (more sophisticated would use AST)
    current_chunk_lines = []
    current_line_start = 1
    
    for i, line in enumerate(lines, 1):
        current_chunk_lines.append(line)
        
        # Check if chunk is large enough (rough token estimate: 1 token ≈ 4 chars)
        chunk_text = '\n'.join(current_chunk_lines)
        estimated_tokens = len(chunk_text) // 4
        
        if estimated_tokens >= chunk_size or i == len(lines):
            # Create chunk
            chunk_id = hashlib.md5(f"{file_path}:{current_line_start}:{i}".encode()).hexdigest()[:12]
            
            chunks.append({
                'id': chunk_id,
                'file': file_path,
                'start_line': current_line_start,
                'end_line': i,
                'content': chunk_text,
                'language': detect_language(file_path)
            })
            
            # Start new chunk with overlap
            overlap_lines = max(0, len(current_chunk_lines) - CHUNK_OVERLAP)
            current_chunk_lines = current_chunk_lines[overlap_lines:]
            current_line_start = i - len(current_chunk_lines) + 1
    
    return chunks


def detect_language(file_path: str) -> str:
    """Detect language from file extension."""
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.tsx': 'typescript', '.jsx': 'javascript', '.java': 'java',
        '.go': 'go', '.rs': 'rust', '.cpp': 'cpp', '.c': 'c',
        '.h': 'c', '.hpp': 'cpp', '.cs': 'csharp', '.rb': 'ruby',
        '.php': 'php', '.scala': 'scala', '.kt': 'kotlin',
        '.swift': 'swift', '.m': 'objective-c', '.sh': 'shell'
    }
    return lang_map.get(ext, 'unknown')


# =============================================================================
# EMBEDDING
# =============================================================================

def get_openai_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding from OpenAI API."""
    try:
        import openai
        
        api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY required for OpenAI embeddings")
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.embeddings.create(
            model=model,
            input=text[:8000]  # Limit input length
        )
        
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"OpenAI embedding failed: {e}")


def get_local_embedding(text: str) -> List[float]:
    """Get embedding from local model (placeholder)."""
    # In production, use sentence-transformers or similar
    # For now, return a mock embedding
    import random
    random.seed(hash(text) % 2**32)
    return [random.random() for _ in range(384)]


# =============================================================================
# INDEX BUILDING
# =============================================================================

def build_rag_index(
    repo: str,
    out: str,
    use_openai: bool = True,
    max_files: int = 500
) -> Dict[str, Any]:
    """
    Build RAG index from repository code.
    
    Args:
        repo: Path to repository
        out: Output directory for index
        use_openai: Use OpenAI embeddings (else local)
        max_files: Maximum files to index
    
    Returns:
        Index metadata
    """
    print(f"Building RAG index...")
    print(f"  Repository: {repo}")
    print(f"  Output: {out}")
    print(f"  Embeddings: {'OpenAI' if use_openai else 'Local'}")
    
    repo_path = Path(repo)
    os.makedirs(out, exist_ok=True)
    
    # Collect files to index
    files_to_index = []
    for root, dirs, files in os.walk(repo_path):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if Path(file).suffix.lower() in INDEXABLE_EXTENSIONS:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(repo_path)
                files_to_index.append(str(rel_path))
        
        if len(files_to_index) >= max_files:
            break
    
    print(f"  Found {len(files_to_index)} files to index")
    
    # Chunk all files
    all_chunks = []
    for file_path in files_to_index:
        full_path = repo_path / file_path
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if len(content) > 100:  # Skip tiny files
                chunks = chunk_file(file_path, content)
                all_chunks.extend(chunks)
        except Exception as e:
            print(f"    Warning: Could not read {file_path}: {e}")
    
    print(f"  Created {len(all_chunks)} chunks")
    
    # Generate embeddings
    print("  Generating embeddings...")
    embeddings = []
    
    embed_fn = get_openai_embedding if use_openai else get_local_embedding
    
    for i, chunk in enumerate(all_chunks):
        try:
            embedding = embed_fn(chunk['content'])
            embeddings.append({
                'id': chunk['id'],
                'embedding': embedding,
                'metadata': {
                    'file': chunk['file'],
                    'start_line': chunk['start_line'],
                    'end_line': chunk['end_line'],
                    'language': chunk['language']
                }
            })
            
            if (i + 1) % 50 == 0:
                print(f"    Embedded {i + 1}/{len(all_chunks)} chunks")
        
        except Exception as e:
            print(f"    Warning: Could not embed chunk {chunk['id']}: {e}")
    
    # Save index
    index_data = {
        'version': '1.0',
        'repo': str(repo_path.absolute()),
        'embedding_model': 'text-embedding-3-small' if use_openai else 'local',
        'chunk_count': len(embeddings),
        'file_count': len(files_to_index)
    }
    
    # Save metadata
    with open(os.path.join(out, 'index_meta.json'), 'w') as f:
        json.dump(index_data, f, indent=2)
    
    # Save chunks (content)
    chunks_data = [{
        'id': c['id'],
        'file': c['file'],
        'start_line': c['start_line'],
        'end_line': c['end_line'],
        'language': c['language'],
        'content': c['content'][:1000]  # Limit stored content
    } for c in all_chunks]
    
    with open(os.path.join(out, 'chunks.json'), 'w') as f:
        json.dump(chunks_data, f, indent=2)
    
    # Save embeddings
    with open(os.path.join(out, 'embeddings.json'), 'w') as f:
        json.dump(embeddings, f)
    
    print(f"\n✓ RAG index saved to {out}")
    print(f"  Chunks: {len(embeddings)}")
    print(f"  Files: {len(files_to_index)}")
    
    return index_data


# =============================================================================
# QUERYING
# =============================================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def query_rag(
    index_dir: str,
    query_code: str,
    top_k: int = 5,
    use_openai: bool = True
) -> List[Dict[str, Any]]:
    """
    Query RAG index for similar code chunks.
    
    Args:
        index_dir: Path to RAG index directory
        query_code: Code snippet to find similar chunks for
        top_k: Number of results to return
        use_openai: Use OpenAI embeddings (must match build)
    
    Returns:
        List of similar chunks with metadata and distance
    """
    index_path = Path(index_dir)
    
    # Load embeddings
    embeddings_path = index_path / 'embeddings.json'
    if not embeddings_path.exists():
        raise FileNotFoundError(f"RAG index not found at {index_dir}")
    
    with open(embeddings_path, 'r') as f:
        embeddings = json.load(f)
    
    if not embeddings:
        return []
    
    # Get query embedding
    embed_fn = get_openai_embedding if use_openai else get_local_embedding
    query_embedding = embed_fn(query_code)
    
    # Compute similarities
    similarities = []
    for emb in embeddings:
        sim = cosine_similarity(query_embedding, emb['embedding'])
        similarities.append({
            'metadata': emb['metadata'],
            'distance': 1.0 - sim,  # Convert similarity to distance
            'similarity': sim
        })
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    return similarities[:top_k]


# =============================================================================
# EVIDENCE PACKING
# =============================================================================

def pack_rag_evidence(
    repo: str,
    rag_dir: str,
    base: str,
    head: str,
    out: str,
    max_results: int = 10,
    use_openai: bool = True
) -> Dict[str, Any]:
    """
    Create RAG-only evidence pack with semantically similar code.
    
    Args:
        repo: Path to repository
        rag_dir: Path to RAG index directory
        base: Base commit SHA
        head: Head commit SHA
        out: Output path for evidence pack
        max_results: Maximum similar chunks per changed file
        use_openai: Use OpenAI embeddings
    
    Returns:
        RAG evidence pack dictionary
    """
    print("Creating RAG evidence pack...")
    
    repo_path = Path(repo)
    
    # Get changed files from git
    result = subprocess.run(
        ['git', 'diff', '--name-only', base, head],
        cwd=repo,
        capture_output=True,
        text=True
    )
    
    changed_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    print(f"  Found {len(changed_files)} changed files")
    
    # Find similar code for each changed file
    all_similar = []
    
    for file_path in changed_files:
        full_path = repo_path / file_path
        
        if not full_path.exists():
            continue
        
        # Check if file is indexable
        if Path(file_path).suffix.lower() not in INDEXABLE_EXTENSIONS:
            continue
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if len(content) < 50:
                continue
            
            # Query for similar code
            similar = query_rag(
                index_dir=rag_dir,
                query_code=content[:2000],  # Use first part of file
                top_k=max_results,
                use_openai=use_openai
            )
            
            for sim in similar:
                # Skip if it's the same file
                if sim['metadata']['file'] != file_path:
                    all_similar.append({
                        **sim['metadata'],
                        'distance': sim['distance'],
                        'similarity': sim.get('similarity', 1.0 - sim['distance']),
                        'related_to': file_path
                    })
        
        except Exception as e:
            print(f"    Warning: Could not process {file_path}: {e}")
    
    # Deduplicate and sort
    seen = set()
    unique_similar = []
    for s in all_similar:
        key = (s['file'], s['start_line'], s['end_line'])
        if key not in seen:
            seen.add(key)
            unique_similar.append(s)
    
    unique_similar.sort(key=lambda x: x['similarity'], reverse=True)
    unique_similar = unique_similar[:max_results * 2]  # Keep top results
    
    # Assemble evidence pack
    evidence = {
        'pr': {
            'base': base,
            'head': head,
            'title': f"Changes from {base[:8]} to {head[:8]}"
        },
        'changed_files': [{'path': f} for f in changed_files],
        'similar_chunks': unique_similar,
        'rag_evidence': {
            'similar_code': unique_similar
        },
        'summary': {
            'files_changed': len(changed_files),
            'similar_chunks_found': len(unique_similar)
        }
    }
    
    # Save evidence pack
    os.makedirs(Path(out).parent, exist_ok=True)
    with open(out, 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print(f"\n✓ RAG evidence pack saved to {out}")
    print(f"  Changed files: {len(changed_files)}")
    print(f"  Similar chunks: {len(unique_similar)}")
    
    return evidence

