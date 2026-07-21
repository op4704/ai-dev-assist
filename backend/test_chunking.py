from app.services.chunking_service import chunk_text

sample = "\n".join([f"line {i}" for i in range(1, 201)])
chunks = chunk_text(sample, chunk_size_tokens=100, overlap_tokens=20)

for c in chunks:
    print(f"chunk {c.chunk_index}: lines {c.start_line}-{c.end_line}, ~{c.token_count} tokens")