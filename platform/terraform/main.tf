resource "azurerm_resource_group" "prod_rg" {
  name     = "rg-${var.resource_prefix}-prod"
  location = var.location
}

resource "azurerm_virtual_network" "prod_vnet" {
  name                = "vnet-${var.resource_prefix}-001"
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

resource "azurerm_key_vault" "prod_vault" {
  name                        = "kv-voltsentinel-prod"
  location                    = azurerm_resource_group.prod_rg.location
  resource_group_name         = azurerm_resource_group.prod_rg.name
  tenant_id                   = var.azure_tenant_id
  sku_name                    = "premium"
  purge_protection_enabled    = true
  enabled_for_disk_encryption = true
}

resource "azurerm_storage_account" "prod_adls" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.prod_rg.name
  location                 = azurerm_resource_group.prod_rg.location
  account_tier             = "Premium"
  account_replication_type = "ZRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true

  network_rules {
    default_action             = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.storage_subnet.id]
    bypass                     = ["AzureServices", "Logging"]
  }
}

resource "azurerm_storage_data_lake_gen2_filesystem" "containers" {
  for_each           = toset(["bronze", "silver", "gold", "quarantine"])
  name               = each.key
  storage_account_id = azurerm_storage_account.prod_adls.id
}

resource "azurerm_data_factory" "prod_adf" {
  name                = "adf-${var.resource_prefix}-prod"
  location            = azurerm_resource_group.prod_rg.location
  resource_group_name = azurerm_resource_group.prod_rg.name
  identity { type = "SystemAssigned" }
}

resource "azurerm_role_assignment" "adf_storage_access" {
  scope                = azurerm_storage_account.prod_adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.prod_adf.identity[0].principal_id
}

resource "azurerm_databricks_workspace" "prod_db" {
  name                        = "dbw-${var.resource_prefix}-prod"
  resource_group_name         = azurerm_resource_group.prod_rg.name
  location                    = azurerm_resource_group.prod_rg.location
  sku                         = "premium"
  managed_resource_group_name = "rg-dbw-managed-voltsentinel"
}

provider "databricks" {
  host = azurerm_databricks_workspace.prod_db.workspace_url
}

resource "databricks_cluster" "production_compute" {
  cluster_name            = "Prod_VoltSentinel_Node"
  spark_version           = "14.3.x-scala2.12"
  node_type_id            = var.databricks_node_type
  autotermination_minutes = 30
  num_workers             = var.databricks_num_workers

  spark_conf = {
    "spark.databricks.delta.preview.enabled" = "true"
  }
}
