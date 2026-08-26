-- WHY: pgvector for RAG; uuid-ossp for ids; pg_trgm for ILIKE fallback search.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
