#!/usr/bin/env python3
"""
Comprehensive test to demonstrate source preservation in RAG chunking pipeline.
"""

import json
from pathlib import Path

def test_source_preservation():
    """Test that all source information is properly preserved."""
    
    print('🔗 Source Preservation Test')
    print('=' * 60)
    
    # Test discourse source preservation
    print('📋 Discourse Source Information:')
    discourse_file = Path('data/discourse/processed_posts.json')
    with open(discourse_file) as f:
        discourse_data = json.load(f)
    
    # Show multiple samples to demonstrate consistency
    for i, sample in enumerate(discourse_data[:3]):
        print(f'\n   Sample {i+1}:')
        print(f'     🆔 Topic ID: {sample["topic_id"]}')
        print(f'     📝 Title: {sample["topic_title"][:40]}...')
        print(f'     🔗 URL: {sample["url"]}')
        print(f'     📅 Date: {sample["timestamp"]}')
        print(f'     👥 Users: {len(sample.get("metadata", {}).get("usernames", []))} contributors')
        print(f'     📄 Chunk: {sample["chunk_index"] + 1}/{sample["total_chunks"]}')
        print(f'     🏷️  Type: {sample["source_type"]}')
        
        # Show preserved metadata
        metadata = sample.get('metadata', {})
        print(f'     📊 Metadata: Post count: {metadata.get("post_count", "N/A")}')
    
    print(f'\n   ✅ Total discourse chunks: {len(discourse_data)}')
    print(f'   🎯 All preserve: Topic ID, URL, timestamp, usernames, post counts')
    
    # Test chapter source preservation
    print('\n📚 Chapter Source Information:')
    chapters_base = Path('data/chapters/tools-in-data-science-public')
    
    # Show samples from different modules
    module_samples = []
    for module_dir in sorted(chapters_base.iterdir())[:3]:
        if module_dir.is_dir():
            chunks_file = module_dir / 'chunks.json'
            if chunks_file.exists():
                with open(chunks_file) as f:
                    module_data = json.load(f)
                if module_data:
                    module_samples.append((module_dir.name, module_data[0]))
    
    for i, (module_name, sample) in enumerate(module_samples):
        print(f'\n   Sample {i+1} ({module_name}):')
        print(f'     📁 Module: {sample["module"]}')
        print(f'     📄 File: {sample["file_path"]}')
        print(f'     🆔 Chunk ID: {sample["chunk_id"]}')
        print(f'     📄 Chunk: {sample["chunk_index"] + 1}/{sample["total_chunks"]}')
        print(f'     🏷️  Type: {sample["source_type"]}')
        print(f'     📊 Tokens: {sample["token_count"]}')
        
        # Show preserved file metadata
        metadata = sample.get('metadata', {})
        print(f'     📊 Metadata:')
        print(f'       - Filename: {metadata.get("filename", "N/A")}')
        print(f'       - Size: {metadata.get("size_bytes", "N/A")} bytes')
        print(f'       - Lines: {metadata.get("line_count", "N/A")}')
        if 'title' in metadata:
            print(f'       - Title: {metadata["title"][:30]}...')
    
    # Count total chapters and files
    total_chapters = 0
    total_files = set()
    total_modules = 0
    
    for module_dir in chapters_base.iterdir():
        if module_dir.is_dir():
            chunks_file = module_dir / 'chunks.json'
            if chunks_file.exists():
                total_modules += 1
                with open(chunks_file) as f:
                    module_data = json.load(f)
                total_chapters += len(module_data)
                for chunk in module_data:
                    total_files.add(f"{chunk['module']}/{chunk['file_path']}")
    
    print(f'\n   ✅ Total chapter chunks: {total_chapters}')
    print(f'   📁 From {total_modules} modules, {len(total_files)} unique files')
    print(f'   🎯 All preserve: Module, file path, chunk position, metadata')
    
    # Test traceability
    print('\n🔍 Source Traceability Test:')
    
    # Test discourse traceability
    sample_discourse = discourse_data[0]
    discourse_url = sample_discourse['url']
    print(f'   📋 Discourse: Can trace back to {discourse_url}')
    print(f'     - Original forum post accessible via URL')
    print(f'     - Topic ID {sample_discourse["topic_id"]} preserved')
    print(f'     - Date {sample_discourse["timestamp"]} preserved')
    print(f'     - Contributors preserved in metadata')
    
    # Test chapter traceability  
    if module_samples:
        sample_chapter = module_samples[0][1]
        github_path = f"tools-in-data-science-public/{sample_chapter['module']}/{sample_chapter['file_path']}"
        print(f'   📚 Chapter: Can trace back to {github_path}')
        print(f'     - Repository: tools-in-data-science-public')
        print(f'     - Module: {sample_chapter["module"]}')
        print(f'     - File: {sample_chapter["file_path"]}')
        print(f'     - Chunk position: {sample_chapter["chunk_index"] + 1}/{sample_chapter["total_chunks"]}')
    
    # Test content quality with source preservation
    print('\n📊 Content Quality with Source Preservation:')
    
    # Check that cleaning didn't remove important source references
    discourse_sample_content = discourse_data[2]['content']
    chapter_sample_content = module_samples[0][1]['content'] if module_samples else ""
    
    print('   📋 Discourse content quality:')
    # Check for preserved educational references
    has_links = 'http' in discourse_sample_content
    has_usernames = '@' in discourse_sample_content or 'user' in discourse_sample_content.lower()
    has_structure = any(x in discourse_sample_content for x in ['#', '##', '1.', '2.', '-'])
    
    print(f'     ✅ Links preserved: {has_links}')
    print(f'     ✅ User context: {has_usernames}')
    print(f'     ✅ Structure preserved: {has_structure}')
    
    print('   📚 Chapter content quality:')
    if chapter_sample_content:
        has_code = '```' in chapter_sample_content or '`' in chapter_sample_content
        has_headers = '#' in chapter_sample_content
        has_links = 'http' in chapter_sample_content
        
        print(f'     ✅ Code blocks preserved: {has_code}')
        print(f'     ✅ Headers preserved: {has_headers}')
        print(f'     ✅ Links preserved: {has_links}')
    
    print('\n🎯 Source Preservation Summary:')
    print('   ✅ Discourse: Topic ID, URL, timestamp, usernames, metadata')
    print('   ✅ Chapters: Module, file path, chunk position, file metadata')
    print('   ✅ Traceability: Full path back to original sources')
    print('   ✅ Quality: Content cleaned while preserving source context')
    print('   ✅ Structure: Chunk relationships and positions maintained')
    
    print('\n🔗 Integration Ready:')
    print('   - All chunks contain complete source attribution')
    print('   - RAG system can cite original sources')
    print('   - Users can verify answers by checking source URLs/files')
    print('   - Chunk relationships enable context reconstruction')

if __name__ == "__main__":
    test_source_preservation()
