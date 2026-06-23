resource "azurerm_eventhub_namespace" "streaming" {
  name                = "evhns-${var.project_name}-${var.environment}-${random_string.storage_suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  sku      = "Standard"
  capacity = 1

  auto_inflate_enabled          = false
  public_network_access_enabled = true

  tags = local.common_tags
}

resource "azurerm_eventhub" "scada_telemetry" {
  name                = "eh-scada-telemetry"
  namespace_name      = azurerm_eventhub_namespace.streaming.name
  resource_group_name = azurerm_resource_group.main.name

  partition_count   = 2
  message_retention = 1
}

resource "azurerm_eventhub_consumer_group" "databricks_bronze" {
  name                = "cg-databricks-bronze"
  namespace_name      = azurerm_eventhub_namespace.streaming.name
  eventhub_name       = azurerm_eventhub.scada_telemetry.name
  resource_group_name = azurerm_resource_group.main.name
}
