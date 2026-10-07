"""Hybrid retrieval combining Knowledge Graph and RAG."""

import json
from typing import Dict, Any, List
from pathlib import Path

from prnote.evidence import load_kg
from prnote.rag import query_rag


def pack_hybrid(
    repo: str,
    kg_dir: str,
    rag_dir: str,
    base: str,
    head: str,
    out: str,
    max_tests: int = 3,
    max_rag_results: int = 5,
    use_openai: bool = True
) -> None:
    """
    Assemble hybrid evidence pack combining KG structure + RAG semantics.
    
    Args:
        repo: Path to repository
        kg_dir: Path to KG directory
        rag_dir: Path to RAG index directory
        base: Base commit SHA
        head: Head commit SHA
        out: Output path for hybrid evidence pack
        max_tests: Maximum tests from KG
        max_rag_results: Maximum semantic matches from RAG
        use_openai: Use OpenAI embeddings for RAG
    """
    print("Assembling hybrid evidence pack...")
    
    # 1. Load KG
    nodes, edges = load_kg(kg_dir)
    
    nodes_by_id = {n['id']: n for n in nodes}
    edges_by_src = {}
    for edge in edges:
        if edge['src_id'] not in edges_by_src:
            edges_by_src[edge['src_id']] = []
        edges_by_src[edge['src_id']].append(edge)
    
    # Find PR node
    pr_node = None
    for node in nodes:
        if node['type'] == 'PR':
            pr_node = node
            break
    
    if not pr_node:
        raise ValueError("No PR node found in KG")
    
    pr_id = pr_node['id']
    pr_props = pr_node['props']
    
    # Initialize evidence pack
    hybrid_evidence = {
        'pr': {
            'base': pr_props.get('base', base),
            'head': pr_props.get('head', head),
            'title': pr_props.get('title', '')
        },
        'kg_evidence': {},      # From graph structure
        'rag_evidence': {},     # From semantic search
        'hybrid_ranking': []    # Combined & ranked results
    }
    
    # 2. Collect KG Evidence (Structural)
    print("  Collecting KG evidence (structure)...")
    
    changed_files = []
    nearest_tests = []
    owners = set()
    
    # Get changed files from KG
    pr_edges = edges_by_src.get(pr_id, [])
    for edge in pr_edges:
        if edge['rel'] == 'touched_file':
            file_id = edge['dst_id']
            file_node = nodes_by_id.get(file_id)
            
            if file_node:
                file_props = file_node['props']
                edge_props = edge['props']
                
                changed_files.append({
                    'path': file_props.get('path', ''),
                    'language': file_props.get('language', ''),
                    'hunks': edge_props.get('hunks', []),
                    'added': edge_props.get('added', 0),
                    'deleted': edge_props.get('deleted', 0)
                })
    
    # Get tests from KG
    test_coverage = []
    changed_file_ids = [f"file:{f['path']}" for f in changed_files]
    
    for node in nodes:
        if node['type'] == 'TestCase':
            test_id = node['id']
            test_props = node['props']
            
            test_edges = edges_by_src.get(test_id, [])
            for edge in test_edges:
                if edge['rel'] == 'covers' and edge['dst_id'] in changed_file_ids:
                    confidence = edge['props'].get('confidence', 0.5)
                    test_coverage.append({
                        'test_id': test_id,
                        'path': test_props.get('file', ''),
                        'name': test_props.get('name', ''),
                        'confidence': confidence,
                        'source': 'kg'
                    })
    
    test_coverage.sort(key=lambda t: t['confidence'], reverse=True)
    nearest_tests = test_coverage[:max_tests]
    
    # Get owners from KG
    for file_id in changed_file_ids:
        for edge in edges:
            if edge['rel'] == 'owns' and edge['dst_id'] == file_id:
                owner_node = nodes_by_id.get(edge['src_id'])
                if owner_node:
                    owners.add(owner_node['props'].get('handle', ''))
    
    hybrid_evidence['kg_evidence'] = {
        'changed_files': changed_files,
        'nearest_tests': nearest_tests,
        'owners': [{'handle': h} for h in sorted(owners)]
    }
    
    # 3. Collect RAG Evidence (Semantic)
    print("  Collecting RAG evidence (semantic)...")
    
    rag_results = []
    
    # For each changed file, find semantically similar code
    for changed_file in changed_files:
        file_path = Path(repo) / changed_file['path']
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract just the changed parts (hunks)
                lines = content.split('\n')
                for hunk in changed_file['hunks']:
                    start = max(0, hunk['start'] - 1)
                    end = min(len(lines), hunk['end'])
                    hunk_content = '\n'.join(lines[start:end])
                    
                    # Query RAG for similar code
                    similar = query_rag(
                        index_dir=rag_dir,
                        query_code=hunk_content,
                        top_k=max_rag_results,
                        use_openai=use_openai
                    )
                    
                    for sim in similar:
                        # Skip if it's the same file (not interesting)
                        if sim['metadata']['file'] != changed_file['path']:
                            rag_results.append({
                                'file': sim['metadata']['file'],
                                'start_line': sim['metadata']['start_line'],
                                'end_line': sim['metadata']['end_line'],
                                'language': sim['metadata']['language'],
                                'distance': sim['distance'],
                                'similarity': 1.0 - sim['distance'] if sim['distance'] else 0.0,
                                'source': 'rag',
                                'related_to': changed_file['path']
                            })
            except Exception as e:
                print(f"    Warning: Could not process {changed_file['path']}: {e}")
    
    # Deduplicate and sort RAG results
    seen = set()
    unique_rag = []
    for r in rag_results:
        key = (r['file'], r['start_line'], r['end_line'])
        if key not in seen:
            seen.add(key)
            unique_rag.append(r)
    
    unique_rag.sort(key=lambda x: x['similarity'], reverse=True)
    hybrid_evidence['rag_evidence'] = {
        'similar_code': unique_rag[:max_rag_results]
    }
    
    # 4. Hybrid Ranking (Combine KG + RAG)
    print("  Combining and ranking results...")
    
    hybrid_ranking = []
    
    # Add KG results with high confidence (structure is reliable)
    for test in nearest_tests:
        hybrid_ranking.append({
            'type': 'test',
            'source': 'kg',
            'score': test['confidence'] * 1.5,  # Boost KG slightly
            'data': test
        })
    
    # Add RAG results
    for similar in unique_rag[:max_rag_results]:
        hybrid_ranking.append({
            'type': 'similar_code',
            'source': 'rag',
            'score': similar['similarity'],
            'data': similar
        })
    
    # Sort by combined score
    hybrid_ranking.sort(key=lambda x: x['score'], reverse=True)
    hybrid_evidence['hybrid_ranking'] = hybrid_ranking
    
    # 5. Save
    import os
    os.makedirs(Path(out).parent, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(hybrid_evidence, f, indent=2)
    
    print(f"✓ Hybrid evidence pack saved to {out}")
    print(f"\nHybrid Summary:")
    print(f"  KG: {len(changed_files)} files, {len(nearest_tests)} tests, {len(owners)} owners")
    print(f"  RAG: {len(unique_rag[:max_rag_results])} similar code chunks")
    print(f"  Combined: {len(hybrid_ranking)} ranked results")










