output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "resource_group_location" {
  value = azurerm_resource_group.main.location
}

output "storage_account_name" {
  value = azurerm_storage_account.lakehouse.name
}

output "storage_filesystems" {
  value = keys(azurerm_storage_data_lake_gen2_filesystem.lakehouse_containers)
}

output "eventhub_namespace_name" {
  value = azurerm_eventhub_namespace.streaming.name
}

output "eventhub_name" {
  value = azurerm_eventhub.scada_telemetry.name
}

output "eventhub_consumer_group_databricks" {
  value = azurerm_eventhub_consumer_group.databricks_bronze.name
}

output "eventhub_kafka_bootstrap_server" {
  value = "${azurerm_eventhub_namespace.streaming.name}.servicebus.windows.net:9093"
}

output "databricks_workspace_name" {
  value = azurerm_databricks_workspace.main.name
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.main.workspace_url
}
