# Capstone Project — Architecture Diagrams

This folder contains the **complex architecture diagrams** for the Enterprise GenAI Document Q&A system (Capstone). The diagrams are written in [Mermaid](https://mermaid.js.org/) and render in GitHub, GitLab, and most Markdown viewers.

The **agent path** is implemented as a **LangChain-style multi-agent pipeline**: **Planner** (planning and safety) → **Retriever** → **Reasoner** (LangChain core messages + shared BaseChatModel) → **Validator**. **Planning** produces a `Plan` (`needs_retrieval`, `planned_query`) that drives whether retrieval runs and what query is sent to the vector store; the orchestrator returns an execution summary (planned query, chunks retrieved, validation result). See [Architecture](../architecture.md) for the full narrative on LangChain agents and planning.

---

## 1. System Context (High-Level)

Shows the system boundary and external actors/integrations.

```mermaid
flowchart TB
    subgraph Users["👤 Users"]
        U[User / Browser]
    end

    subgraph Capstone["Enterprise GenAI Document Q&A (Capstone)"]
        subgraph Frontend["Frontend"]
            SPA[React SPA<br/>Vite · TypeScript · Tailwind]
            SPA --> Ask[Ask Page]
            SPA --> Upload[Upload Page]
            SPA --> Docs[Documents Page]
        end

        subgraph Backend["Backend"]
            API[FastAPI API<br/>/api/v1]
        end
    end

    subgraph External["External Systems"]
        OpenAI[OpenAI / Compatible API<br/>LLM + Embeddings]
        Chroma[ChromaDB<br/>Vector Store]
        SQLite[(SQLite<br/>Metadata)]
    end

    U <-->|HTTPS / REST| SPA
    SPA <-->|/api/v1/*| API
    API <-->|Embeddings, Chat| OpenAI
    API <-->|Vector CRUD, Search| Chroma
    API <-->|Document metadata| SQLite
```

---

## 2. Layered Architecture (All Components)

Full stack from client down to data and external services.

```mermaid
flowchart TB
    subgraph Client["🖥️ Client Layer"]
        subgraph ReactApp["React Application"]
            Layout[Layout + Navigation]
            AskPage[AskPage]
            UploadPage[UploadPage]
            DocumentsPage[DocumentsPage]
            UploadZone[UploadZone]
            AnswerPanel[AnswerPanel]
        end
        APIClient[lib/api.ts<br/>REST client]
    end

    subgraph API["🔌 API Layer (FastAPI)"]
        Health[GET /health]
        DocUpload[POST /documents/upload]
        DocList[GET /documents]
        DocDetail[GET /documents/:id]
        QueryRAG[POST /query]
        QueryAgent[POST /agents/query]
    end

    subgraph Application["⚙️ Application Layer"]
        subgraph Ingestion["Ingestion Pipeline"]
            IngestionSvc[IngestionService]
            ParsingSvc[ParsingService]
            ChunkingSvc[ChunkingService]
            EmbeddingSvc[EmbeddingService]
            VectorStoreSvc[VectorStoreService]
        end
        subgraph RAG["RAG Pipeline"]
            RAGService[RAGService]
        end
        subgraph Agents["Agent Workflow"]
            Orchestrator[AgentOrchestrator]
            Planner[PlannerAgent]
            Retriever[RetrieverAgent]
            Reasoner[ReasonerAgent]
            Validator[ValidatorAgent]
        end
    end

    subgraph Data["💾 Data Layer"]
        MetaStore[MetadataStore]
        FileStorage[(File Storage<br/>uploads/)]
    end

    subgraph External["🌐 External"]
        OpenAI_API[OpenAI API<br/>LLM + Embeddings]
        ChromaDB[(ChromaDB<br/>Vector Index)]
        SQLiteDB[(SQLite<br/>documents table)]
    end

    ReactApp --> APIClient
    APIClient --> Health
    APIClient --> DocUpload
    APIClient --> DocList
    APIClient --> DocDetail
    APIClient --> QueryRAG
    APIClient --> QueryAgent

    DocUpload --> IngestionSvc
    DocList --> MetaStore
    DocDetail --> MetaStore
    QueryRAG --> RAGService
    QueryAgent --> Orchestrator

    IngestionSvc --> ParsingSvc
    ParsingSvc --> ChunkingSvc
    ChunkingSvc --> EmbeddingSvc
    EmbeddingSvc --> VectorStoreSvc
    IngestionSvc --> MetaStore
    IngestionSvc --> FileStorage

    RAGService --> VectorStoreSvc
    RAGService --> OpenAI_API

    Orchestrator --> Planner
    Orchestrator --> Retriever
    Orchestrator --> Reasoner
    Orchestrator --> Validator
    Retriever --> VectorStoreSvc
    Reasoner --> OpenAI_API

    VectorStoreSvc --> ChromaDB
    MetaStore --> SQLiteDB
```

---

## 3. Document Ingestion Flow (Sequence)

End-to-end flow from upload to indexed document.

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant FE as Frontend
    participant API as Documents API
    participant Ing as IngestionService
    participant Parse as ParsingService
    participant Chunk as ChunkingService
    participant Emb as EmbeddingService
    participant VS as VectorStore
    participant MS as MetadataStore
    participant Chroma as ChromaDB
    participant SQL as SQLite

    U->>FE: Select file & upload
    FE->>API: POST /documents/upload (multipart)
    API->>API: Validate type & size
    API->>Ing: validate_and_store_upload() → ingest_file()

    Ing->>MS: upsert(PENDING)
    MS->>SQL: INSERT/UPDATE
    Ing->>Parse: parse_file()
    Parse-->>Ing: ParseResult (text, pages/sheets)
    Ing->>Chunk: chunk_parse_result()
    Chunk-->>Ing: DocumentChunk[]
    Ing->>Emb: embed_documents()
    Emb->>Emb: OpenAI or sentence-transformers
    Emb-->>Ing: vectors
    Ing->>VS: add_chunks()
    VS->>Chroma: add(ids, embeddings, metadata)
    Ing->>MS: update_status, chunk_count
    MS->>SQL: UPDATE
    Ing-->>API: document_id, status, chunk_count
    API-->>FE: UploadResponse
    FE-->>U: Success message
```

---

## 4. RAG vs Agent Query (Decision Flow)

How a question is routed and processed.

```mermaid
flowchart LR
    subgraph Frontend
        Q[User question]
        Toggle{Use agent<br/>workflow?}
    end

    subgraph RAGPath["RAG path"]
        RAG[POST /query]
        RAGService[RAGService]
        Safe1[is_safe_query]
        Search1[vector_store.search]
        Prompt1[Build prompt]
        LLM1[LLM]
        Cite1[Build citations]
    end

    subgraph AgentPath["Agent path"]
        Agent[POST /agents/query]
        Orch[AgentOrchestrator]
        P[Planner]
        R[Retriever]
        Reas[Reasoner]
        V[Validator]
    end

    Q --> Toggle
    Toggle -->|No| RAG
    Toggle -->|Yes| Agent
    RAG --> RAGService
    RAGService --> Safe1 --> Search1 --> Prompt1 --> LLM1 --> Cite1
    Agent --> Orch --> P --> R --> Reas --> V
```

---

## 5. Agent Pipeline Detail (Planner → Validator)

Internal steps of the agent workflow.

```mermaid
flowchart TB
    subgraph Input
        Question[User question]
    end

    subgraph Orchestrator["AgentOrchestrator"]
        direction TB
        P[PlannerAgent]
        R[RetrieverAgent]
        Reas[ReasonerAgent]
        V[ValidatorAgent]
    end

    subgraph PlannerLogic["Planner"]
        P1[Safety check]
        P2[needs_retrieval?]
        P3[planned_query]
        P1 --> P2 --> P3
    end

    subgraph RetrieverLogic["Retriever"]
        R1[vector_store.search]
        R2[Top-k chunks + scores]
        R1 --> R2
    end

    subgraph ReasonerLogic["Reasoner"]
        Re1[Build context from chunks]
        Re2[LangChain ChatOpenAI]
        Re3[Answer text]
        Re1 --> Re2 --> Re3
    end

    subgraph ValidatorLogic["Validator"]
        V1[Check citations]
        V2[Support status]
        V3[ValidationResult]
        V1 --> V2 --> V3
    end

    Question --> P
    P --> PlannerLogic
    PlannerLogic --> R
    R --> RetrieverLogic
    RetrieverLogic --> Reas
    Reas --> ReasonerLogic
    ReasonerLogic --> V
    V --> ValidatorLogic
    ValidatorLogic --> Response[AgentQueryResponse<br/>+ execution_summary]
```

---

## 6. Backend Module Dependency Graph

How backend packages depend on each other (simplified).

```mermaid
flowchart LR
    subgraph api["api/routes"]
        health[health]
        documents[documents]
        query[query]
    end

    subgraph services["services"]
        ingestion[ingestion]
        parsing[parsing]
        chunking[chunking]
        embedding[embedding]
        vector_store[vector_store]
    end

    subgraph rag["rag"]
        pipeline[pipeline]
    end

    subgraph agents["agents"]
        orchestrator[orchestrator]
        planner[planner]
        retriever[retriever]
        reasoner[reasoner]
        validator[validator]
    end

    subgraph db["db"]
        metadata_store[metadata_store]
    end

    subgraph core["core"]
        config[config]
    end

    documents --> ingestion
    query --> pipeline
    query --> orchestrator
    ingestion --> parsing
    ingestion --> chunking
    ingestion --> embedding
    ingestion --> vector_store
    ingestion --> metadata_store
    pipeline --> vector_store
    pipeline --> embedding
    orchestrator --> planner
    orchestrator --> retriever
    orchestrator --> reasoner
    orchestrator --> validator
    retriever --> vector_store
    reasoner --> config
    config -.-> core
```

---

## 7. Data Stores and Their Use

Where data lives and who reads/writes it.

```mermaid
flowchart TB
    subgraph Stores["Data Stores"]
        subgraph FS["File system"]
            Uploads[uploads/]
        end
        subgraph Chroma["ChromaDB"]
            Col[Collection]
            Col --> Emb[Embeddings]
            Col --> Meta[Chunk metadata]
        end
        subgraph SQL["SQLite"]
            T[documents table]
        end
    end

    subgraph Writers["Writers"]
        Ing[IngestionService]
    end

    subgraph Readers["Readers"]
        DocAPI[Documents API]
        RAG[RAGService]
        Ret[RetrieverAgent]
    end

    Ing --> Uploads
    Ing --> Col
    Ing --> T
    DocAPI --> T
    RAG --> Col
    Ret --> Col
```

---

## LangChain agents and planning (reference)

| Agent | Role | Planning / outputs |
|-------|------|--------------------|
| **PlannerAgent** | Safety check; decide if retrieval needed; normalize question | **Plan**: `needs_retrieval`, `planned_query`, `reasoning_summary`, `error` |
| **RetrieverAgent** | Vector search with `planned_query` | Top-k `(DocumentChunk, score)` |
| **ReasonerAgent** | Build context; LangChain core (SystemMessage, HumanMessage) + BaseChatModel; synthesize answer | Answer text |
| **ValidatorAgent** | Check grounding and citations | **ValidationResult**: `passed`, `support_status`, `summary`, `issues` |

The **orchestrator** runs these in sequence and returns **AgentQueryResponse** with **execution_summary** (planned query, retrieval performed, chunks count, validation passed, step summaries).

---

## Summary

| Diagram | Purpose |
|--------|---------|
| **1. System Context** | High-level boundary and external integrations |
| **2. Layered Architecture** | All components across client, API, application, data, external |
| **3. Document Ingestion** | Sequence of steps from upload to indexed document |
| **4. RAG vs Agent** | Routing and flow for simple RAG vs agent workflow |
| **5. Agent Pipeline** | Planner → Retriever → Reasoner → Validator detail |
| **6. Backend Module Dependency** | Internal package dependencies |
| **7. Data Stores** | Which services use which stores |

For narrative and flows, see the main [Architecture](architecture.md) doc (parent `docs/` folder).
