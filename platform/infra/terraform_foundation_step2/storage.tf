resource "random_string" "storage_suffix" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_storage_account" "lakehouse" {
  name                     = "stvs${random_string.storage_suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # Required for ADLS Gen2 hierarchical namespace.
  is_hns_enabled = true

  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  tags = local.common_tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "lakehouse_containers" {
  for_each = toset([
    "bronze",
    "silver",
    "gold",
    "quarantine",
    "observability"
  ])

  name               = each.key
  storage_account_id = azurerm_storage_account.lakehouse.id
}
