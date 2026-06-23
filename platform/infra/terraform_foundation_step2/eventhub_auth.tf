resource "azurerm_eventhub_namespace_authorization_rule" "scada_producer_send" {
  name                = "scada-producer-send"
  namespace_name      = azurerm_eventhub_namespace.streaming.name
  resource_group_name = azurerm_resource_group.main.name

  listen = false
  send   = true
  manage = false
}

resource "azurerm_eventhub_namespace_authorization_rule" "databricks_consumer_listen" {
  name                = "databricks-consumer-listen"
  namespace_name      = azurerm_eventhub_namespace.streaming.name
  resource_group_name = azurerm_resource_group.main.name

  listen = true
  send   = false
  manage = false
}
