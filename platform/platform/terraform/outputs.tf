output "resource_group_name" { value = azurerm_resource_group.prod_rg.name }
output "storage_account_name" { value = azurerm_storage_account.prod_adls.name }
output "databricks_workspace_url" { value = azurerm_databricks_workspace.prod_db.workspace_url }
output "data_factory_name" { value = azurerm_data_factory.prod_adf.name }
