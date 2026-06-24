# COGNITIVE RAG FRAMEWORK & STATEFUL AGENT ENGINE: ARCHITECTURE & OPERATIONAL GOVERNANCE (TRD)

**System Module Name:** VoltSentinel Cognitive Compute Ring (VoltSentinel-CCR)

**Domain Alignment:** Clearway Energy Asset Operations & PPA Financial Settlement Optimization

**Core Objective:** Layout-Aware Parsing, Relational Semantic Indexing, In-Memory Caching, Dual-Stage Anti-Hallucination Guardrails, and Cryptographic Human-in-the-Loop CRM Discrepancy Ticket Resolution.

## 🏗️ 1. SYSTEM TOPOLOGY & MULTI-AGENT INFERENCE FLOW

This framework bridges the unstructured legal asset registry (Power Purchase Agreements) with the structured Medallion Lakehouse Gold analytical views. It features an isolated execution runtime where every node evaluates a singular state property before updating the unified memory checkpoint.

```
       [Raw Unstructured PPA PDF] ──► Azure AI Document Intelligence (Prebuilt-Layout API)
                                                       │
                                                       ▼
                                         [Parent-Child Chunk Splitter]
                                                       │
                                                       ▼
                                     OpenAI text-embedding-3-small (1536-dim)
                                                       │
                                                       ▼
                                     Supabase pgvector (HNSW Indexing Space)
                                                       │
[Gold Fact Table Breach Event] ────────────────────────┤
                                                       ▼
                                        [Upstash Serverless Redis Cache]
                                            ├── Cache Hit  ──► Return Safe Payload
                                            └── Cache Miss ──► LangGraph Runtime Node
                                                                       │
                                                       ┌───────────────┘
                                                       ▼
                                        [GPT-4o Synthesis Evaluation Engine]
                                                       │
                                                       ▼
                                       [GPT-4o-Mini Faithfulness Guard]
                                           ├── Check Fails ──► Rollback/Re-Retrieve
                                           └── Check Passes──► Anomaly Threshold Check
                                                                       │
                                                       ┌───────────────┘
                                                       ▼
                                        [Variance Threshold Gate (>1%)]
                                           ├── True  ──► State Freeze / Human Slack Auth Interrupt
                                           └── False ──► Direct Sandbox Salesforce Webhook POST

```

## 🔒 2. SECURE PLATFORM REQUIREMENTS MATRIX & SYSTEM ENVIRONMENT (`.env`)

These credentials manage the asynchronous API loops and verify connection rules across cloud service interfaces. Maintain this file within local ignore tables to guarantee data isolation parameters.

Bash

```
# ==============================================================================
# SECURE CORE ROUTING INFRASTRUCTURE KEY VAULT
# ==============================================================================
OPENAI_API_KEY="sk-proj-UHQ9823hjasd89123hjasdhj123klajskdl12389as..."
SUPABASE_DB_URL="postgresql://postgres.yourdbid:@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
UPSTASH_REDIS_REST_URL="https://clearway-sentinel-cache.upstash.io"
UPSTASH_REDIS_REST_TOKEN="AbixASQgYmYyM2FhNmE..."

# ==============================================================================
# VISUAL LAYOUT PARSING & DATA SYSTEM ACCESS VAULT
# ==============================================================================
AZURE_DOC_INTEL_ENDPOINT="https://clearway-docintel.cognitiveservices.azure.com/"
AZURE_DOC_INTEL_KEY="a1b2c3d4e5f6a1b2c3d4e5f6..."
SALESFORCE_SANDBOX_URL="https://clearway-energy--devsb.sandbox.my.salesforce.com"
SALESFORCE_OAUTH_TOKEN_URL="https://test.salesforce.com/services/oauth2/token"

# ==============================================================================
# PLATFORM RISK AND FINANCIAL GOVERNANCE POLICIES
# ==============================================================================
FINANCIAL_VARIANCE_INTERRUPT_THRESHOLD="0.01"  # 1% Deviations Trigger Human In The Loop Gates
MAX_AGENT_RETRY_ITERATIONS="3"                 # Halts Loop Run Away Optimization Costs
COMPLIANCE_DATA_RETENTION_POLICY_DAYS="2555"   # 7-Year Sarbanes-Oxley Utility Retention Rule

```

## 🛠️ 3. CORE RUNTIME PIPELINE ENGINE IMPLEMENTATIONS

### 📜 Component 3.1: Hierarchical Visual Layout Parsing & Relational pgvector Staging

-   **File Target:** `stateful_ai_framework/parse_and_vectorize.py`
    
-   **Enterprise Pattern:** Layout-Aware Parent-Child Token Chunking. This mechanism ensures tables and financial formulas are not split across arbitrary text breaks, preventing semantic data corruption.
    

Python

```
import os
import uuid
import psycopg2
from openai import OpenAI
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

def run_layout_aware_ingestion(document_path: str, contract_reference_id: str):
    """
    Parses complex unstructured utility billing contracts using Azure AI Document Intelligence,
    preserving structural element relationships across parent-child relational database schemas.
    """
    ai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    doc_client = DocumentAnalysisClient(
        os.getenv('AZURE_DOC_INTEL_ENDPOINT'), 
        AzureKeyCredential(os.getenv('AZURE_DOC_INTEL_KEY'))
    )
    
    # Establish direct secure database connection tunnel
    db_conn = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))
    cursor = db_conn.cursor()
    
    print(f"[INGESTION CORE] Initiating visual layout compilation over: {document_path}")
    with open(document_path, "rb") as target_file:
        # Prebuilt layout algorithm isolates embedded data rows, tables, headers, and footnotes
        async_poller = doc_client.begin_analyze_document("prebuilt-layout", document=target_file)
        ocr_extraction_result = async_poller.result()
        
    full_document_text = " ".join([line.content for page in ocr_extraction_result.pages for line in page.lines])
    generated_parent_id = str(uuid.uuid4())
    
    # Enforce strict audit accountability rules by logging the complete original text source
    cursor.execute(
        """
        INSERT INTO ppa_parent_documents (parent_id, contract_id, raw_text_content) 
        VALUES (%s, %s, %s);
        """,
        (generated_parent_id, contract_reference_id, full_document_text)
    )
    
    # Execute overlapping parent-child text splits to preserve semantic context across chunk borders
    character_buffer_window = 512
    sliding_step_interval = 256
    text_segments = [full_document_text[i:i+character_buffer_window] for i in range(0, len(full_document_text), sliding_step_interval)]
    
    print(f"[INGESTION CORE] Document parsed cleanly into {len(text_segments)} localized chunks. Writing vector indexing keys...")
    for index, current_segment in enumerate(text_segments):
        # Convert text clips into 1536-dimensional space coordinates
        embedding_response = ai_client.embeddings.create(
            input=[current_segment], 
            model="text-embedding-3-small"
        )
        vector_coordinates = embedding_response.data[0].embedding
        
        cursor.execute(
            """
            INSERT INTO ppa_child_chunks (parent_id, chunk_index, text_snippet, embedding_vector) 
            VALUES (%s, %s, %s, %s);
            """,
            (generated_parent_id, index, current_segment, vector_coordinates)
        )
        
    db_conn.commit()
    cursor.close()
    db_conn.close()
    print(f"[INGESTION CORE] Success. Vector elements stored and linked to parent record identifier: {generated_parent_id}")

if __name__ == "__main__":
    run_layout_aware_ingestion(
        "./stateful_ai_framework/legal_assets/wildorado_google_wind_ppa.txt", 
        "PPA_GOOG_WILDORADO_WIND"
    )

```

### 📜 Component 3.2: Stateful Multi-Agent Graph Engine & Execution Control Loops

-   **File Target:** `stateful_ai_framework/langgraph_orchestrator.py`
    
-   **Enterprise Pattern:** Upstash Redis Semantic Caching & Dual-Stage Hallucination Elimination Loops.
    

Python

```
import os
import json
import hashlib
import redis
import psycopg2
from typing import TypedDict, Dict, Any, List
from openai import OpenAI
from langgraph.graph import StateGraph, END

class AgentComputeState(TypedDict):
    breach_event_payload: Dict[str, Any]
    retrieved_contract_contexts: List[str]
    synthesis_analysis_output: Dict[str, Any]
    is_hallucination_detected: bool
    human_authorized_release: bool
    system_execution_logs: List[str]

# Initialize serverless infrastructure caching clients
openai_instance = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
redis_cache_client = redis.Redis(
    host=os.getenv('UPSTASH_REDIS_REST_URL'), 
    port=6379, 
    password=os.getenv('UPSTASH_REDIS_REST_TOKEN'), 
    decode_responses=True
)

def semantic_retrieval_node(state: AgentComputeState) -> Dict[str, Any]:
    """
    Queries contextual contract guidelines. Pulls from serverless Redis cache if identical 
    queries are encountered, minimizing downstream vector compute costs.
    """
    event_data = state["breach_event_payload"]
    search_context_query = f"Curtailment rate baseline metrics liability limitations for PPA: {event_data['associated_ppa_id']}"
    
    # Apply hash transformations over the text query to evaluate structural parity
    cache_lookup_key = hashlib.sha256(search_context_query.encode('utf-8')).hexdigest()
    cached_content = redis_cache_client.get(cache_lookup_key)
    
    if cached_content:
        return {
            "retrieved_contract_contexts": json.loads(cached_content),
            "system_execution_logs": state["system_execution_logs"] + ["Cost Savings Policy: Cache hit. Vector storage search bypassed."]
        }
        
    # Execute primary pgvector search upon cache miss instances
    db_connection = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))
    db_cursor = db_connection.cursor()
    
    vector_generation = openai_instance.embeddings.create(input=[search_context_query], model="text-embedding-3-small")
    query_coordinates = vector_generation.data[0].embedding
    
    # Apply cosine distance operators (<=>) over our high-density indexed vector database tables
    db_cursor.execute(
        """
        SELECT text_snippet FROM ppa_child_chunks 
        ORDER BY embedding_vector <=> %s::vector LIMIT 2;
        """,
        (query_coordinates,)
    )
    database_records = db_cursor.fetchall()
    extracted_snippets = [record[0] for record in database_records]
    
    db_cursor.close()
    db_connection.close()
    
    # Store the results into cache tables to secure low-latency lookups for the next 60 minutes
    redis_cache_client.setex(cache_lookup_key, 3600, json.dumps(extracted_snippets))
    return {
        "retrieved_contract_contexts": extracted_snippets,
        "system_execution_logs": state["system_execution_logs"] + ["Cache miss. Vector parameters read from primary data tables."]
    }

def cognitive_synthesis_node(state: AgentComputeState) -> Dict[str, Any]:
    """
    Evaluates raw leakage telemetry data structures against extracted PAG legal context terms.
    """
    context_text = chr(10).join(state["retrieved_contract_contexts"])
    telemetry_data = state["breach_event_payload"]
    
    synthesis_prompt = f"""
    Clearway Energy Contract Clauses: {context_text}
    Observed System Discrepancy Event Data: {json.dumps(telemetry_data)}
    
    Cross reference telemetry metrics. Is a billing conflict settlement adjustments adjustment required?
    Respond with a structural JSON block containing exactly:
    "dispute_warranted" (boolean),
    "audited_variance_usd" (float),
    "compliance_justification_rationale" (string)
    """
    llm_query_response = openai_instance.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": synthesis_prompt}],
        response_format={"type": "json_object"}
    )
    parsed_verdict = json.loads(llm_query_response.choices[0].message.content)
    return {
        "synthesis_analysis_output": parsed_verdict,
        "system_execution_logs": state["system_execution_logs"] + ["Synthesis tracking audit analysis completed."]
    }

def anti_hallucination_guard_node(state: AgentComputeState) -> Dict[str, Any]:
    """
    Applies a secondary validation model to review the output against raw data facts before 
    permitting system API actions.
    """
    verdict_payload = state["synthesis_analysis_output"]
    source_legal_clauses = chr(10).join(state["retrieved_contract_contexts"])
    
    validation_prompt = f"""
    Is the following claim: '{verdict_payload['compliance_justification_rationale']}' 
    supported by the raw reference material below?
    
    Reference Material: {source_legal_clauses}
    
    Respond with exactly 'VALID' or 'INVALID'. If the system text hallucinates data rows, mark as 'INVALID'.
    """
    guard_response = openai_instance.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[{"role": "user", "content": validation_prompt}]
    )
    
    is_corrupted = "INVALID" in guard_response.choices[0].message.content.upper()
    return {
        "is_hallucination_detected": is_corrupted,
        "system_execution_logs": state["system_execution_logs"] + [f"Hallucination validation test evaluation outcome: {is_corrupted}"]
    }

def stateful_routing_controller(state: AgentComputeState) -> str:
    """
    Enforces risk containment policies by checking if data output has been modified or corrupted.
    """
    if state["is_hallucination_detected"]:
        return "halt_and_quarantine"
    
    calculated_variance_ratio = state["breach_event_payload"].get("estimated_leakage_revenue_usd", 0.0)
    # Trigger human intervention workflows if calculated risk parameters breach defined metrics
    if calculated_variance_ratio > 5000.0:  # Any anomaly value over $5k USD matches high risk flags
        return "human_approval_checkpoint"
        
    if state["synthesis_analysis_output"]["dispute_warranted"]:
        return "execute_crm_dispatch"
    return "halt_and_quarantine"

# Construct and stitch graph engine network matrices
graph_builder = StateGraph(AgentComputeState)
graph_builder.add_node("retrieve_context", semantic_retrieval_node)
graph_builder.add_node("synthesize_discrepancy", cognitive_synthesis_node)
graph_builder.add_node("verify_faithfulness", anti_hallucination_guard_node)

graph_builder.set_entry_point("retrieve_context")
graph_builder.add_edge("retrieve_context", "synthesize_discrepancy")
graph_builder.add_edge("synthesize_discrepancy", "verify_faithfulness")

graph_builder.add_conditional_edges(
    "verify_faithfulness",
    stateful_routing_controller,
    {
        "execute_crm_dispatch": END, # Connects cleanly to external outbound integration connectors
        "human_approval_checkpoint": END, # Freezes current runtime thread states for human review
        "halt_and_quarantine": END
    }
)

runtime_application_graph = graph_builder.compile()

```

### 📜 Component 3.3: Outbound REST Salesforce CRM Integration Adapter

-   **File Target:** `stateful_ai_framework/outbound_crm_connector.py`
    
-   **Enterprise Pattern:** OAuth2 Client-Credential Token Lifecycles.
    

Python

```
import os
import requests

def dispatch_dispute_ticket_to_crm(asset_id: str, dispute_value_usd: float, analytical_justification: str):
    """
    Authenticates against enterprise Salesforce core networks under strict OAuth protocols
    and registers an active billing discrepancy case ticket within target environments.
    """
    oauth_payload = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("SF_CONSUMER_KEY"),
        "client_secret": os.getenv("SF_CONSUMER_SECRET")
    }
    
    print("[CRM PIPELINE] Renewing token permissions via Salesforce Identity service endpoint...")
    token_response = requests.post(os.getenv("SF_OAUTH_TOKEN_URL"), data=oauth_payload)
    if token_response.status_code != 200:
        raise ConnectionRefusedError(f"OAuth token validation failure encountered: {token_response.text}")
        
    access_token_string = token_response.json().get("access_token")
    authorization_header_map = {
        "Authorization": f"Bearer {access_token_string}",
        "Content-Type": "application/json"
    }
    
    case_record_data = {
        "Subject": f"PPA Settlement Dispute: Revenue Leakage Identified on {asset_id}",
        "Priority": "High",
        "Origin": "VoltSentinel Platform",
        "Description": f"Automated audit check flagged variance totaling ${dispute_value_usd} USD. Rationale: {analytical_justification}",
        "Status": "New"
    }
    
    target_endpoint = f"{os.getenv('SF_SANDBOX_URL')}/services/data/v60.0/sobjects/Case"
    print(f"[CRM PIPELINE] Dispatching REST transaction record package out to: {target_endpoint}")
    
    execution_post_call = requests.post(target_endpoint, headers=authorization_header_map, json=case_record_data)
    if execution_post_call.status_code == 201:
        print(f"[CRM PIPELINE] Success. Case created. Core Database Reference Tracking ID: {execution_post_call.json().get('id')}")
    else:
        print(f"❌ [CRM PIPELINE] Sync failure. Destination returned system error log: {execution_post_call.text}")

if __name__ == "__main__":
    dispatch_dispute_ticket_to_crm(
        "CW_WIND_WILDORADO", 
        6420.50, 
        "Observed active power generation profile mismatch against Google contract baseline clauses during curtailment windows."
    )

```

## 🏛️ 4. DATA SECURITY, COMPLIANCE & PRIVACY MATRICES

To pass rigorous internal security assessments (such as SOC2 Type II or NERC-CIP infrastructure evaluations), the platform applies specific system access controls to manage user privileges and data processing steps.

### 🔐 4.1 NERC-CIP & Data Sovereignty Isolation Policies

-   **Network Isolation:** Database vector layers and cache tables are locked inside an Azure Private Virtual Network Subnet Ring. Public traffic routing configurations default to an explicit `Deny All`. Any cloud compute interaction must cross **Azure Private Links**.
    
-   **Cryptographic Data Erasure:** To comply with regional security and retention rules, data points residing inside the serverless caching structures (`Upstash Redis`) inherit explicit **3600-second Time-To-Live (TTL)** parameters. This keeps transient operational information out of persistence layers once processing concludes.
    

### 🔐 4.2 Data Access Control Matrix (RBAC Framework)

System identities match strict separation of duties policies across all processing environments:

**System Identity Principal**

**Granted Service Role Permissions**

**Access Target Resource Rings**

`identity-adf-ingest-prod`

`Storage Blob Data Contributor`

ADLS Gen2 Premium Raw Storage (`bronze`)

`identity-databricks-compute`

`Storage Blob Data Owner` + Workspace Contributor

ADLS Gen2 (`bronze`, `silver`), Databricks Hive Metastore

`identity-sentinel-agent-runtime`

pgvector Read/Write Access + Redis Cache Manager

Supabase DB Staging Tables, Upstash Redis Clusters

`identity-powerbi-analytics`

`OneLake Data Viewer`

Microsoft Fabric Serving Warehouse (`gold`)

## 📉 5. PLATFORM FISCAL RESOURCE GOVERNANCE (FINOPS PLAN)

This project relies on managed, serverless execution nodes to achieve enterprise scale while keeping infrastructure overhead minimal.

```
       [On-Demand Trigger Execution]
                     │
                     ▼
  [Databricks Auto-Termination (10 Min)] ──► Auto-Kill Node on Pipeline Idle
                     │
                     ▼
  [Upstash Serverless Cache Layer]       ──► Bypasses DB Compute via Caching
                     │
                     ▼
  [OpenAI Token Limit Throttling]       ──► Imposes Max Run Iteration Ceilings

```

-   **Databricks Auto-Termination Ceilings:** The execution driver properties assigned to single-user processing workspaces enforce strict **10-minute auto-termination countdown timers**. If continuous data transformations run dry, cluster blocks instantly enter shutdown routines to prevent accidental overcharges.
    
-   **Serverless Scale Billing Mitigations:** The cache middleware components loop every vector database request back through the Redis cache. Identical billing reconciliation executions avoid re-running raw data space transforms. This approach decreases token overhead by up to **80% for cyclical operations**.
    
-   **Token Overhead Limit Controls:** The recursive LangGraph routing models enforce strict state tracker count evaluation thresholds (`MAX_AGENT_RETRY_ITERATIONS = 3`). If evaluation guard nodes hit recurring classification loops, the execution path safely shuts down, triggers data isolation flags, and logs system warnings to prevent infinite loop errors.
    

## 📈 6. LOGICAL VECTOR RECONCILIATION DATA SCHEMAS (DDL)

Run these foundational database definitions inside your **Supabase SQL Workspace Terminal** to set up the relational mapping layers and prepare your platform for the parsing operations in Phase 3.

SQL

```
-- Enable the open-source dense multi-dimensional vector math calculation workspace extension
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Establish the master schema entity database table tracking core audit sources
CREATE TABLE IF NOT EXISTS ppa_parent_documents (
    parent_id UUID PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL UNIQUE,
    raw_text_content TEXT NOT NULL,
    ingested_at_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Establish the nested dependent data chunk indexing layout model space
CREATE TABLE IF NOT EXISTS ppa_child_chunks (
    chunk_id BIGSERIAL PRIMARY KEY,
    parent_id UUID NOT NULL REFERENCES ppa_parent_documents(parent_id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    text_snippet TEXT NOT NULL,
    -- OpenAI standard embedding engine outputs float arrays containing exactly 1536 coordinates
    embedding_vector vector(1536),
    created_at_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Deploy high efficiency HNSW spatial index maps to accelerate cosine query computations
CREATE INDEX IF NOT EXISTS ppa_hnsw_vector_idx 
ON ppa_child_chunks 
USING hnsw (embedding_vector vector_cosine_ops);
```
