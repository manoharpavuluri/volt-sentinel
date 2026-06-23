variable "azure_tenant_id" { type = string }
variable "location" { type = string default = "Central US" }
variable "resource_prefix" { type = string default = "volt-sentinel" }
variable "storage_account_name" { type = string default = "stvoltsentinelprod" }
variable "databricks_node_type" { type = string default = "Standard_D8s_v5" }
variable "databricks_num_workers" { type = number default = 2 }
