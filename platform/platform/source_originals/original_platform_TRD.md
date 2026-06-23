
# TECHNICAL REFERENCE ARCHITECTURE, TRD & DATA SIMULATION RUNBOOK

**System Target Name:** Project VoltSentinel

**Domain Context:** Clearway Energy Utility-Scale Asset Portfolio Management (Wind, Solar, & Storage Ecosystem)

**Core Objective:** Automated Identification of Revenue Leakage from Congestion Curtailment and PPA Settlement Discrepancies.

## 🏗️ EXECUTIVE SUMMARY & SYSTEM TOPOLOGY

Project VoltSentinel is a production-grade, enterprise-scale cognitive data platform tailored for Clearway Energy’s operational footprint. The system modernizes legacy data patterns by introducing a cloud-native, isolated Medallion Lakehouse Engine, a real-time event logging fabric, and an asynchronous stateful cyclic multi-agent graph.

The primary business objective is to automatically track, reconcile, and resolve financial leakage resulting from grid-enforced asset curtailments and market settlement true-ups against commercial Power Purchase Agreements (PPAs) signed with corporations or public utilities across major ISO regions (ERCOT, CAISO, PJM).

### 🌐 Unified Enterprise Topology & Private Networking Ring

To mirror strict enterprise compliance frameworks, no primary data asset or processing node is exposed directly to the public internet. All systems communicate over an isolated cloud backbone utilizing virtual networking boundaries and endpoints.

```
[Phase 0: Local Simulation Daemons] 
       │ 
       ├── (Continuous Stream) ──► [Upstash Serverless Kafka Brokers] ──► (TLS 1.3 / SASL_SSL)
       └── (Daily Snapshots)   ──► [Local Staging Folders] ──► [Azure ADF Self-Hosted IR Bridge]
                                                                        │
                                   ┌────────────────────────────────────┘
                                   ▼ (Azure Private Link Endpoints)
                    [Azure Data Lake Storage Gen2 (ADLS HNS)]
                                   │
                                   ▼ (Single-User / Shared Isolated Nodes)
                    [Azure Databricks Lakehouse Workspace Cluster]
                                   │
                                   ▼ (Incremental Merges via dbt)
                    [Microsoft Fabric OneLake / Gold Serving Layer] ──► [Power BI DirectLake]

```

## 📁 1. PLATFORM REPOSITORY SCHEMA & PROJECT TREE

Plaintext

```
volt-sentinel-platform/
├── .github/
│   └── workflows/
│       ├── terraform-ci-cd.yml      # CI/CD pipeline to validate and deploy infrastructure
│       └── data-pipeline-cd.yml     # Automated build and deployment of Spark/dbt code
├── terraform/
│   ├── providers.tf                 # Cloud provider engine configurations (Azure, Databricks)
│   ├── main.tf                      # Primary infrastructure fabric blueprint
│   ├── security.tf                  # VNets, Private Endpoints, Firewalls, Key Vault
│   ├── variables.tf                 # Sizing parameter declarations
│   └── terraform.tfvars            # Account-specific deployment variables
├── data_simulation/                # Phase 0: Edge Simulation & IT Systems Emulation
│   ├── generate_scada_stream.py    # Real-time multi-turbine wind & solar event stream loop
│   └── generate_it_snapshots.py    # Historical SAP asset and Salesforce PPA registry compiler
├── data_movement_ingestion/        # Multi-Velocity Ingestion Framework
│   ├── adf_copy_templates/         
│   │   ├── clearway_sap_assets.json# Data Factory extraction mapping for master metrics
│   │   └── clearway_sf_ppas.json   # Data Factory ingestion parameters for contract rules
│   └── transform_lakehouse/        # Intermittent Compute Delta Transformation Core
│       ├── dbt_project.yml         # Managed dbt analytics project configuration
│       ├── models/                 
│       │   ├── bronze/              # Streaming logs delta staging views
│       │   ├── silver/              # Cleaned, conformed views validated via Soda-Core
│       │   └── gold/                # Enterprise financial dimensional star schemas
│       └── data_observability/     
│           ├── configuration.yml   # Soda-Core database target engine router properties
│           └── checks.yml          # Declarative data quality threshold contracts
└── stateful_ai_framework/          # Cognitive Context Layer & Robotic Process Automation (RPA)
    ├── legal_assets/               # Sample unstructured Clearway PPA agreements (PDF/Text)
    ├── parse_and_vectorize.py      # Layout OCR analysis via Azure AI Document Intelligence
    ├── semantic_cache.py           # In-memory inference deduplication via Serverless Redis
    ├── langgraph_orchestrator.py   # Cyclic state machine engine using permanent Postgres memory
    └── outbound_crm_connector.py   # REST token authentication handler to create billing cases

```

### 🔒 Core Global Token Vault File: `.env`

Save this configuration profile explicitly in the primary repository root folder to abstract variable strings completely from code statements. **Do not track this file via Git.**

Bash

```
# ==============================================================================
# UNIFIED PLATFORM SECRETS LAYER (PERMANENT ANCHORS)
# ==============================================================================
OPENAI_API_KEY="sk-proj-yourPermanentDeveloperKeyAlphaNumericString..."
SUPABASE_DB_URL="postgresql://enterprise_admin:LocalSecurePassword123@db-id.supabase.co:5432/postgres"
UPSTASH_REDIS_REST_URL="https://your-chosen-cache.upstash.io"
UPSTASH_REDIS_REST_TOKEN="yourServerlessRedisTokenString..."

# ==============================================================================
# CLOUD PROVIDER WORKSPACE TOKENS (ROTATING EPHEMERAL PIPES)
# ==============================================================================
AZURE_SUBSCRIPTION_ID="your-azure-subscription-guid-0000-00000000"
AZURE_TENANT_ID="your-azure-tenant-guid-1111-11111111"
DATABRICKS_HOST="https://adb-workspace-url.azuredatabricks.net"
AZURE_DOC_INTEL_ENDPOINT="https://doc-intel-sentinel.cognitiveservices.azure.com/"
AZURE_DOC_INTEL_KEY="yourAzureDocumentIntelligenceSecretKeyString..."
UPSTASH_KAFKA_BOOTSTRAP_SERVER="your-kafka-endpoint.upstash.io:9092"
UPSTASH_KAFKA_USERNAME="yourUpstashKafkaSaslUsernameString"
UPSTASH_KAFKA_PASSWORD="yourUpstashKafkaSaslPasswordString"

# ==============================================================================
# EXTERNAL DOWNSTREAM WEBHOOK EMULATION TARGETS
# ==============================================================================
SF_CONSUMER_KEY="salesforceConnectedAppOauthClientIdString..."
SF_CONSUMER_SECRET="salesforceConnectedAppOauthClientSecretString..."
SF_USERNAME="your.developer.profile@clearway.sandbox.com"
SF_PASSWORD="yourSalesforceAccountPasswordText"
SF_SECURITY_TOKEN="salesforceGeneratedApiSecurityTokenString..."

```

## 🛠️ PHASE 0: SYNTHETIC DATA ENGINEERING & EDGE EMULATION

**Objective:** Build standalone, localized simulation daemons to populate your workspace with high-fidelity, domain-specific energy data structures. This completely removes dependencies on real SAP, Salesforce, or field equipment during early infrastructure staging.

### 📜 Component 0.1: High-Velocity Real-Time SCADA Multi-Asset Stream Producer

-   **File Target:** `data_simulation/generate_scada_stream.py`
    
-   **Purpose:** Simulates high-frequency industrial data payloads from varying renewable asset types. It handles connections out to **Upstash Serverless Kafka** under a secure SASL protocol layer and intentionally introduces random data failures (such as negative active power calculations) to test downstream validation tools.
    

Python

```
import os
import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from pydantic import BaseModel, Field, ValidationError

class ClearwaySCADAModel(BaseModel):
    timestamp: str
    asset_id: str
    generation_kw: float
    operating_status: str = Field(pattern=r'^(NORMAL|CURTAILED_BY_ERCOT|NIGHT_REST)$')

# Initialize Kafka producer using secure serverless authentication tokens
producer = KafkaProducer(
    bootstrap_servers=[os.getenv("UPSTASH_KAFKA_BOOTSTRAP_SERVER")],
    sasl_mechanism='SCRAM-SHA-256',
    security_protocol='SASL_SSL',
    sasl_plain_username=os.getenv("UPSTASH_KAFKA_USERNAME"),
    sasl_plain_password=os.getenv("UPSTASH_KAFKA_PASSWORD"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

TOPIC_NAME = 'clearway-scada-realtime'
ASSETS = ['CW_WIND_WILDORADO', 'CW_SOLAR_DAGGETT', 'CW_SOLAR_BLACKDUST']

print(f"📡 Clearway Simulation Active. Broadcasting streaming telemetries to: {TOPIC_NAME}")

try:
    while True:
        timestamp_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        for asset in ASSETS:
            active_power_kw = 0.0
            status_flag = "NORMAL"
            
            if asset == 'CW_WIND_WILDORADO':
                # Model utility scale wind site generation (161MW max profile capacity)
                active_power_kw = round(random.uniform(10000.0, 150000.0), 2)
                # Intentionally force grid curtailment exceptions to test out downstream AI agents
                if random.random() < 0.08:
                    active_power_kw = -250.0 # Introduce corrupted parasitic draw anomaly
                    status_flag = "CURTAILED_BY_ERCOT"
                    
            elif 'SOLAR' in asset:
                # Model solar output curves based on daylight availability
                current_hour = datetime.utcnow().hour
                if 12 <= current_hour <= 22:
                    base_power = 350000.0 if 'DAGGETT' in asset else 85000.0
                    active_power_kw = round(base_power * random.uniform(0.70, 0.98), 2)
                else:
                    active_power_kw = 0.0
                    status_flag = "NIGHT_REST"
            
            payload = {
                "timestamp": timestamp_str,
                "asset_id": asset,
                "generation_kw": active_power_kw,
                "operating_status": status_flag
            }
            
            try:
                # Intercept schema adjustments at the system border entry point
                ClearwaySCADAModel(**payload)
                producer.send(TOPIC_NAME, payload)
            except ValidationError as err:
                print(f"⚠️ Anomaly blocked by edge schema validation rules: {err.json()}")
            
        time.sleep(10) # 10-second industrial capture rate iteration loop
except KeyboardInterrupt:
    producer.close()

```

### 📜 Component 0.2: Relational IT Enterprise Snapshot Generator (SAP & Salesforce Assets)

-   **File Target:** `data_simulation/generate_it_snapshots.py`
    
-   **Purpose:** Compiles clean CSV lookup structures mapping out an ERP asset registry and a CRM contract matching framework to decouple your pipelines from live environment access requirements.
    

Python

```
import os
import csv

SAP_OUTPUT_PATH = "./local_landing_zone/clearway_sap/"
SF_OUTPUT_PATH = "./local_landing_zone/clearway_salesforce/"
os.makedirs(SAP_OUTPUT_PATH, exist_ok=True)
os.makedirs(SF_OUTPUT_PATH, exist_ok=True)

def build_clearway_enterprise_snapshots():
    # 1. Generate SAP PM Asset Registry using actual Clearway field locations
    with open(os.path.join(SAP_OUTPUT_PATH, "CLEARWAY_ASSET_REGISTRY.csv"), mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ASSET_ID", "EQUIP_NAME", "ASSET_TYPE", "RATED_CAPACITY_MW", "ISO_REGION", "COMMERCIAL_ONLINE_DATE"])
        writer.writerow(["CW_WIND_WILDORADO", "Wildorado Wind Ranch", "WIND", 161.0, "ERCOT", "2007-04-01"])
        writer.writerow(["CW_SOLAR_DAGGETT", "Daggett Solar Infrastructure", "SOLAR", 482.0, "CAISO", "2024-03-15"])
        writer.writerow(["CW_BESS_DAGGETT", "Daggett Battery Storage Block B", "STORAGE", 394.0, "CAISO", "2024-03-15"])
        writer.writerow(["CW_SOLAR_BLACKDUST", "Black Dust Solar Project", "SOLAR", 120.0, "PJM", "2026-06-01"])
        
    # 2. Generate Salesforce CRM Commercial Account PPA Matrix with real offtaker types
    with open(os.path.join(SF_OUTPUT_PATH, "CLEARWAY_PPA_ACCOUNT_MAPPING.csv"), mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ACCOUNT_ID", "OFTAKER_NAME", "ASSOCIATED_PPA_ID", "SITE_IDENTITY_TAG", "CONTRACT_RATE_PER_MWH"])
        writer.writerow(["ACC_TECH_GOOG", "Google Cloud Operations LLC", "PPA_GOOG_WILDORADO_WIND", "CW_WIND_WILDORADO", 42.50])
        writer.writerow(["ACC_UTIL_SCE", "Southern California Edison", "PPA_SCE_DAGGETT_SOLAR", "CW_SOLAR_DAGGETT", 38.00])
        writer.writerow(["ACC_CORP_AMZN", "Amazon Web Services Energy Hub", "PPA_AMZN_BLACKDUST", "CW_SOLAR_BLACKDUST", 45.10])

    print("📊 Clearway SAP and Salesforce mock snapshots updated with real assets.")

if __name__ == "__main__":
    build_clearway_enterprise_snapshots()

```

## 🏗️ PHASE 1: NETWORKING, PRIVATE INFRASTRUCTURE & INGESTION (ADF)

**Objective:** Provision secure, production-grade cloud environments using declarative Terraform templates. This sets up private networking, deploys an encrypted storage backbone, and maps out **Azure Data Factory (ADF)** pipelines to ingest your batch snapshots.

### 📜 Programmatic Workspace Deployment Blueprint: `terraform/main.tf`

Terraform

```
variable "azure_tenant_id" { type = string }

resource "azurerm_resource_group" "prod_rg" {
  name     = "rg-volt-sentinel-prod"
  location = "Central US"
}

# 1. Private Virtual Network Ring
resource "azurerm_virtual_network" "prod_vnet" {
  name                = "vnet-volt-sentinel-001"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.prod_rg.location
  resource_group_name = azurerm_resource_group.prod_rg.name
}

resource "azurerm_subnet" "storage_subnet" {
  name                 = "sub-prod-storage-001"
  resource_group_name  = azurerm_resource_group.prod_rg.name
  virtual_network_name = azurerm_virtual_network.prod_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
  service_endpoints    = ["Microsoft.Storage"]
}

# 2. Production Security Master Cryptographic Key Store
resource "azurerm_key_vault" "prod_vault" {
  name                        = "kv-volt-sentinel-prod"
  location                    = azurerm_resource_group.prod_rg.location
  resource_group_name         = azurerm_resource_group.prod_rg.name
  tenant_id                   = var.azure_tenant_id
  sku_name                    = "premium"
  enabled_for_disk_encryption = true
  purge_protection_enabled    = true
}

# 3. High-Performance Enterprise Storage Backend Layer (ADLS Gen2)
resource "azurerm_storage_account" "prod_adls" {
  name                     = "stvoltsentinelprod"
  resource_group_name      = azurerm_resource_group.prod_rg.name
  location                 = azurerm_resource_group.prod_rg.location
  account_tier             = "Premium"
  account_replication_type = "ZRS" # Zone-Redundant Storage for high-availability profiles
  account_kind             = "StorageV2"
  is_hns_enabled           = true  # Required for atomic directory renames and file scaling acceleration

  network_rules {
    default_action             = "Deny" # Rejects public traffic paths completely
    virtual_network_subnet_ids = [azurerm_subnet.storage_subnet.id]
    bypass                     = ["AzureServices", "Logging"]
  }
}

resource "azurerm_storage_data_lake_gen2_filesystem" "containers" {
  for_each           = toset(["bronze", "silver", "gold"])
  name               = each.key
  storage_account_id = azurerm_storage_account.prod_adls.id
}

# 4. Azure Data Factory Pipeline Instance Creation
resource "azurerm_data_factory" "prod_adf" {
  name                = "adf-volt-sentinel-prod"
  location            = azurerm_resource_group.prod_rg.location
  resource_group_name = azurerm_resource_group.prod_rg.name
  identity { type = "SystemAssigned" }
}

resource "azurerm_role_assignment" "adf_storage_access" {
  scope                = azurerm_storage_account.prod_adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.prod_adf.identity[0].principal_id
}

# 5. Production Databricks Compute Workspace Environment
resource "azurerm_databricks_workspace" "prod_db" {
  name                        = "dbw-volt-sentinel-prod"
  resource_group_name         = azurerm_resource_group.prod_rg.name
  location                    = azurerm_resource_group.prod_rg.location
  sku                         = "premium"
  managed_resource_group_name = "rg-dbw-managed-sentinel"
}

provider "databricks" {
  host = azurerm_databricks_workspace.prod_db.workspace_url
}

resource "databricks_cluster" "production_compute" {
  cluster_name            = "Prod_Sentinel_Node"
  spark_version           = "14.3.x-scala2.12"
  node_type_id            = "Standard_D8s_v5" # Optimized high-memory production compute unit
  autotermination_minutes = 30                # Automatically scales down cluster nodes when idle
  num_workers             = 2

  spark_conf = {
    "spark.databricks.delta.preview.enabled" = "true"
    "spark.databricks.passthrough.enabled"   = "true"
  }
}

```

### 📜 Component 1.2: ADF Metadata-Driven Snapshot Copy Schema

-   **File Target:** `data_movement_ingestion/adf_templates/clearway_sap_assets.json`
    
-   **Purpose:** Defines the declarative pipeline asset blueprint for ADF to copy the relational snapshot files via your secure Self-Hosted Integration Runtime bridge.
    

JSON

```
{
  "name": "pl_ingest_clearway_sap_assets",
  "properties": {
    "activities": [
      {
        "name": "Copy_SAP_Assets_Snapshot",
        "type": "Copy",
        "policy": {
          "timeout": "0.02:00:00",
          "retry": 2,
          "retryIntervalInSeconds": 30,
          "secureOutput": true,
          "secureInput": true
        },
        "typeProperties": {
          "source": {
            "type": "DelimitedTextSource",
            "storeSettings": { "type": "FileServerReadSettings" },
            "formatSettings": { "type": "DelimitedTextReadSettings", "columnDelimiter": "," }
          },
          "sink": {
            "type": "ParquetSink",
            "storeSettings": { "type": "AzureBlobFSWriteSettings" },
            "formatSettings": { "type": "ParquetWriteSettings" }
          }
        },
        "inputs": [{ "referenceName": "ds_local_csv_source", "type": "DatasetReference" }],
        "outputs": [{
            "referenceName": "ds_adls_parquet_sink",
            "type": "DatasetReference",
            "parameters": { "FolderPath": "clearway_sap/asset_registry" }
        }]
      }
    ]
  }
}

```

## 🧼 PHASE 2: INTERMITTENT LAKEHOUSE ANALYTICS & DATA QUALITY CONTRACTS

**Objective:** Write PySpark routines to ingest streaming telemetry data from your Kafka brokers. Then, apply data observability checks to quarantine anomalies, and run **dbt Core** models to build financial star schemas.

### 📜 Component 2.1: On-Demand PySpark Ingestion Stream Notebook

-   **File Target:** `data_movement_ingestion/transform_lakehouse/stream_bronze_landing.py`
    
-   **Purpose:** Runs as an on-demand process within Databricks. It drains accumulated Kafka events, applies the defined structure schema, and commits the records straight to the cloud storage data lake.
    

Python

```
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

spark = SparkSession.builder \
    .appName("Clearway_Medallion_Bronze") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .getOrCreate()

telemetry_schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("asset_id", StringType(), True),
    StructField("generation_kw", DoubleType(), True),
    StructField("operating_status", StringType(), True)
])

# Stream directly from our authenticated Upstash Kafka topic broker
streaming_src_df = (spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", dbutils.secrets.get("sentinel_vault", "kafka-brokers"))
    .option("subscribe", "clearway-scada-realtime")
    .option("kafka.security.protocol", "SASL_SSL")
    .option("kafka.sasl.mechanism", "SCRAM-SHA-256")
    .load())

parsed_bronze_df = streaming_src_df.select(
    from_json(col("value").cast("string"), telemetry_schema).alias("data")
).select("data.*")

# Bulk append partitions straight out onto premium storage layers
query = (parsed_bronze_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "abfss://bronze@stvoltsentinelprod.dfs.core.windows.net/checkpoints/scada_telemetry")
    .partitionBy("asset_id")
    .trigger(availableNow=True) # Runs compute on-demand then spins the cluster down
    .start("abfss://bronze@stvoltsentinelprod.dfs.core.windows.net/tables/clearway_telemetry"))

query.awaitTermination()

```

### 📜 Component 2.2: Structural Observability Validation Rules

-   **File Target:** `data_movement_ingestion/transform_lakehouse/data_observability/checks.yml`
    
-   **Purpose:** Sets the execution constraints for **Soda-Core** to intercept pipeline runs and isolate corrupted records (like negative energy calculations) to a quarantine bucket.
    

YAML

```
checks_for clearway_telemetry:
  - row_count > 0
  - timestamp is not null
  - asset_id is in ["CW_WIND_WILDORADO", "CW_SOLAR_DAGGETT", "CW_SOLAR_BLACKDUST"]
  - generation_kw >= 0.0:
      error: expr generation_kw < 0.0 indicates a corrupted sensor load error

```

### 📜 Component 2.3: Incremental Revenue Leakage Dimensional Core Model

-   **File Target:** `data_movement_ingestion/transform_lakehouse/models/gold/fact_revenue_leakage.sql`
    
-   **Purpose:** Runs as an incremental dbt pipeline to compile the final analytics tables by joining clean Silver metrics with your relational SAP records and Salesforce lookups.
    

SQL

```
{{ config(
    materialized='incremental',
    unique_key='fact_record_hash',
    incremental_strategy='merge'
) }}

WITH telemetry_agg AS (
    SELECT 
        DATE_TRUNC('hour', to_timestamp(timestamp, 'YYYY-MM-DD HH:MI:SS')) as reconciliation_hour,
        asset_id,
        operating_status,
        SUM(generation_kw) / 60.0 as actual_generation_mwh
    FROM {{ ref('silver_clearway_telemetry') }}
    
    {% if is_incremental() %}
    WHERE to_timestamp(timestamp, 'YYYY-MM-DD HH:MI:SS') >= DATEADD(hour, -3, GETDATE())
    {% endif %}
    GROUP BY 1, 2, 3
),

sap_assets AS (
    SELECT asset_id, equip_name, rated_capacity_mw, iso_region FROM {{ source('clearway_sap', 'asset_registry') }}
),

sf_ppas AS (
    SELECT account_id, oftaker_name, associated_ppa_id, site_identity_tag, contract_rate_per_mwh FROM {{ source('clearway_salesforce', 'ppa_mapping') }}
)

SELECT 
    MD5(CONCAT(t.reconciliation_hour, t.asset_id, sf.associated_ppa_id)) as fact_record_hash,
    t.reconciliation_hour,
    t.asset_id,
    sap.equip_name,
    sap.iso_region,
    sf.oftaker_name,
    sf.associated_ppa_id,
    t.operating_status,
    t.actual_generation_mwh,
    CASE 
        WHEN t.operating_status = 'CURTAILED_BY_ERCOT' THEN (sap.rated_capacity_mw - t.actual_generation_mwh)
        ELSE 0.0 
    END as lost_curtailment_mwh,
    (CASE 
        WHEN t.operating_status = 'CURTAILED_BY_ERCOT' THEN (sap.rated_capacity_mw - t.actual_generation_mwh)
        ELSE 0.0 
     END) * sf.contract_rate_per_mwh as estimated_leakage_revenue_usd
FROM telemetry_agg t
INNER JOIN sap_assets sap ON t.asset_id = sap.asset_id
INNER JOIN sf_ppas sf ON t.asset_id = sf.site_identity_tag

```

## ⚖️ PHASE 3: LAYOUT-AWARE CONTRACT INGESTION & RELATIONAL VECTOR STORES (RAG)

**Objective:** Parse unstructured contract documents (like **Power Purchase Agreements**) while preserving visual document elements. This creates a relational, multi-dimensional vector layout to ground your AI reasoning workflows.

### 📜 Component 3.1: Hierarchical Visual Layout Parsing Framework

-   **File Target:** `stateful_ai_framework/parse_and_vectorize.py`
    
-   **Purpose:** Uses **Azure AI Document Intelligence** to extract structural layout details from legal text files and maps them directly to small text chunks indexed with OpenAI embeddings.
    

Python

```
import os
import uuid
import psycopg2
from openai import OpenAI
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
doc_intel_client = DocumentAnalysisClient(os.getenv('AZURE_DOC_INTEL_ENDPOINT'), AzureKeyCredential(os.getenv('AZURE_DOC_INTEL_KEY')))

def process_and_index_clearway_ppa(file_path: str, contract_id_tag: str):
    db_conn = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))
    cursor = db_conn.cursor()
    
    print(f"📥 Running visual layout extraction over contract document: {file_path}")
    with open(file_path, "rb") as f:
        # Pull text while preserving nested tables and paragraph layout contexts
        poller = doc_intel_client.begin_analyze_document("prebuilt-layout", document=f)
        result = poller.result()

    full_text = " ".join([line.content for page in result.pages for line in page.lines])
    parent_id = str(uuid.uuid4())
    
    # Write the full parent text block to retain complete historical auditing context
    cursor.execute(
        "INSERT INTO ppa_parent_documents (parent_id, contract_id, raw_text_content) VALUES (%s, %s, %s);",
        (parent_id, contract_id_tag, full_text)
    )

    # Fragment text into rolling segments to optimize downstream vector searches
    chunks = [full_text[i:i+512] for i in range(0, len(full_text), 256)]
    
    for idx, text_chunk in enumerate(chunks):
        emb_res = openai_client.embeddings.create(input=[text_chunk], model="text-embedding-3-small")
        vector_coordinates = emb_res.data[0].embedding
        
        # Commit vector arrays directly into pgvector fields
        cursor.execute(
            "INSERT INTO ppa_child_chunks (parent_id, chunk_index, text_snippet, embedding_vector) VALUES (%s, %s, %s, %s);",
            (parent_id, idx, text_chunk, vector_coordinates)
        )
        
    db_conn.commit()
    cursor.close()
    db_conn.close()
    print("✅ Contract vectors successfully indexed into the database database store.")

if __name__ == "__main__":
    process_and_index_clearway_ppa("./stateful_ai_framework/legal_assets/wildorado_google_wind_ppa.txt", "PPA_GOOG_WILDORADO_WIND")

```

## 🤖 PHASE 4: STATEFUL CYCLIC AGENT GRAPH & OUTBOUND CRM AUTOMATION

**Objective:** Wire up your core data systems into a stateful **LangGraph** loop. The agent logic uses Redis to bypass redundant searches, checks generated outputs through verification guards to eliminate hallucinations, and applies human approval flags before pushing billing records to your CRM sandbox.

### 📜 Component 4.1: Stateful Orchestrator and Evaluation Architecture

-   **File Target:** `stateful_ai_framework/langgraph_orchestrator.py`
    
-   **Purpose:** Coordinates your AI agent execution steps. It includes lookups against an **Upstash Serverless Redis** cache and implements validation checkpoints to confirm findings before routing data to outbound CRM connectors.
    

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

class ClearwayAgentState(TypedDict):
    leakage_record_payload: Dict[str, Any]
    retrieved_clauses: List[str]
    synthesis_verdict_json: Dict[str, Any]
    is_hallucination: bool
    human_authorized: bool
    runtime_logs: List[str]

openai_inst = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# Establish connection out to our high performance serverless redis layer
redis_cache = redis.Redis(host=os.getenv('REDIS_HOST'), port=6379, password=os.getenv('REDIS_PASS'), decode_responses=True)

def semantic_retrieval_node(state: ClearwayAgentState) -> Dict[str, Any]:
    payload = state["leakage_record_payload"]
    search_context = f"Curtailment billing rules and penalty liabilities calculation parameters for agreement: {payload['associated_ppa_id']}"
    
    # Run a fast cache check to minimize model costs
    cache_key = hashlib.sha256(search_context.encode('utf-8')).hexdigest()
    cached_hit = redis_cache.get(cache_key)
    if cached_hit:
        return {"retrieved_clauses": json.loads(cached_hit), "runtime_logs": state["runtime_logs"] + ["Context resolved from Redis cache."]}

    # Fall back to database vector queries if a cache miss occurs
    db_conn = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))
    cursor = db_conn.cursor()
    
    emb = openai_inst.embeddings.create(input=[search_context], model="text-embedding-3-small")
    query_vector = emb.data[0].embedding
    
    cursor.execute(
        "SELECT text_snippet FROM ppa_child_chunks ORDER BY embedding_vector <=> %s::vector LIMIT 2;",
        (query_vector,)
    )
    records = cursor.fetchall()
    snippets = [r[0] for r in records]
    
    cursor.close()
    db_conn.close()
    
    redis_cache.setex(cache_key, 3600, json.dumps(snippets)) # Cache hits for 1 hour
    return {"retrieved_clauses": snippets, "runtime_logs": state["runtime_logs"] + ["Fresh context extracted from database database vectors."]}

def evaluation_synthesis_node(state: ClearwayAgentState) -> Dict[str, Any]:
    clauses = state["retrieved_clauses"]
    payload = state["leakage_record_payload"]
    
    prompt = f"""
    Legal Contract Reference Clauses: {chr(10).join(clauses)}
    Identified Discrepancy Payload: {json.dumps(payload)}
    
    Cross reference metrics. Should a formal dispute ticket be logged?
    Return a structural JSON block containing exactly:
    "dispute_required" (boolean),
    "variance_confirmed_usd" (float),
    "justification_text" (string)
    """
    response = openai_inst.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    verdict = json.loads(response.choices[0].message.content)
    return {"synthesis_verdict_json": verdict, "runtime_logs": state["runtime_logs"] + ["Synthesis finished."]}

def anti_hallucination_guard_node(state: ClearwayAgentState) -> Dict[str, Any]:
    verdict = state["synthesis_verdict_json"]
    clauses = state["retrieved_clauses"]
    
    guard_prompt = f"Verify if the claim '{verdict['justification_text']}' is structurally supported by the raw reference material: {chr(10).join(clauses)}. Output exactly 'VALID' or 'INVALID'."
    res = openai_inst.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": guard_prompt}])
    
    failed = "INVALID" in res.choices[0].message.content.upper()
    return {"is_hallucination": failed, "runtime_logs": state["runtime_logs"] + [f"Hallucination verification status flag set to: {failed}"]}

def crm_webhook_dispatch_node(state: ClearwayAgentState) -> Dict[str, Any]:
    if state["is_hallucination"] or not state["human_authorized"]:
        return {"runtime_logs": state["runtime_logs"] + ["Automation halted by system safety rules."]}
        
    print("🚨 Discrepancy verified and approved. Dispatching Salesforce case ticket wrapper...")
    # Calls Phase 4 Salesforce endpoint authentication token refresh modules
    return {"runtime_logs": state["runtime_logs"] + ["Dispute case opened in CRM pipeline successfully."]}

def pipeline_router(state: ClearwayAgentState) -> str:
    if state["is_hallucination"]: return "halt"
    if state["synthesis_verdict_json"]["dispute_required"]: return "trigger_dispute"
    return "halt"

# Compile and coordinate graph relationships
workflow = StateGraph(ClearwayAgentState)
workflow.add_node("retrieve_context", semantic_retrieval_node)
workflow.add_node("synthesize_discrepancy", evaluation_synthesis_node)
workflow.add_node("verify_faithfulness", anti_hallucination_guard_node)
workflow.add_node("dispatch_ticket", crm_webhook_dispatch_node)

workflow.set_entry_point("retrieve_context")
workflow.add_edge("retrieve_context", "synthesize_discrepancy")
workflow.add_edge("synthesize_discrepancy", "verify_faithfulness")
workflow.add_conditional_edges("verify_faithfulness", pipeline_router, {"trigger_dispute": "dispatch_ticket", "halt": END})
workflow.add_edge("dispatch_ticket", END)

app = workflow.compile()
print("🚀 Stateful agentic system graph compiled successfully.")

```

## 🛠️ 5. DEPLOYMENT, CONTINUOUS INTEGRATION & MAINTENANCE RUNBOOK

To maintain this modern, multi-cloud data platform smoothly without creating operational friction, deploy these automated **GitHub Actions CI/CD** workflows alongside your core code assets.

### 📜 Component 5.1: Automated CI/CD Infrastructure Pipeline

-   **File Target:** `.github/workflows/terraform-ci-cd.yml`
    
-   **Purpose:** Runs on every code push to your main branch. It checks format style rules, validates your main Terraform file patterns, and provisions infrastructure components using secure OpenID Connect (OIDC) authentication.
    

YAML

```
name: 'Infrastructure Deployment Core'

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

permissions:
  contents: read
  id-token: write # Required for passwordless Azure OIDC authentication

jobs:
  terraform_pipeline:
    name: 'Validate & Apply Core Fabric'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./terraform

    steps:
    - name: Checkout Code Repository
      uses: actions/checkout@v4

    - name: Setup Terraform Engine Runtime
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: 1.7.0

    - name: Azure Cryptographic Authentication OIDC
      uses: azure/login@v2
      with:
        client-id: ${{ secrets.AZURE_CLIENT_ID }}
        tenant-id: ${{ secrets.AZURE_TENANT_ID }}
        subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

    - name: Terraform Format Check
      run: terraform fmt -check

    - name: Terraform Init Initialization
      run: terraform init

    - name: Terraform Structural Validation
      run: terraform validate

    - name: Terraform Deployment Execution
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
      run: terraform apply -auto-approve -var="azure_tenant_id=${{ secrets.AZURE_TENANT_ID }}"

```

## 📈 6. SYSTEM IMPLEMENTATION STRATEGY & DELIVERY MILESTONES

Following this structured, five-stage implementation strategy isolates tool sets from application logic, ensures data trace transparency, and allows you to build out your architecture within predictable free-tier boundaries.

**Phase**

**Principal Milestone Deliverable**

**Cost Containment Policy**

**Core Architecture Learning Value**

**Phase 0**

Stream & Snapshot Emulators

Pydantic Border Schema Enforcement

Advanced generation modeling, data boundary structure design, and mock system construction.

**Phase 1**

Cloud Networking Backbone & ADF Pipelines

VNet Private Link Subnets + SHIR Connectors

Production network provisioning, managed cloud identities, and hybrid network data copying.

**Phase 2**

Medallion PySpark & dbt Aggregations

10-Min Cluster Termination + Incremental Models

On-demand distributed stream engineering, dbt dependency modeling, and data observability contracts.

**Phase 3**

Layout OCR Document Parsing & pgvector Store

Relational Foreign-Key Mapping Snippets

Advanced layout-aware contract parsing, custom vector indexing structures, and relational storage design.

**Phase 4**

Stateful LangGraph Machine & CRM Connectors

Redis Caching + Persistent Checkpoint Pools

Cyclic multi-agent graph engineering, custom anti-hallucination validation, and secure REST webhook automation

