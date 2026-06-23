resource "azurerm_databricks_workspace" "main" {
  name                        = "dbw-${var.project_name}-${var.environment}-${random_string.storage_suffix.result}"
  resource_group_name         = azurerm_resource_group.main.name
  location                    = azurerm_resource_group.main.location
  sku                         = "premium"
  managed_resource_group_name = "rg-managed-dbw-${var.project_name}-${var.environment}-${random_string.storage_suffix.result}"

  tags = local.common_tags
}
