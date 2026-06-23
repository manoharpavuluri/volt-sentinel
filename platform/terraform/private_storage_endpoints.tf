/*
Production hardening snippet for ADLS Gen2 private access.
Use this after the MVP works and after private DNS is validated from ADF/Databricks/SHIR networks.

This is intended to supplement, not blindly replace, main.tf.
*/

resource "azurerm_subnet" "private_endpoint_subnet" {
  name                 = "sub-prod-private-endpoints-001"
  resource_group_name  = azurerm_resource_group.prod_rg.name
  virtual_network_name = azurerm_virtual_network.prod_vnet.name
  address_prefixes     = ["10.0.10.0/24"]

  private_endpoint_network_policies = "Disabled"
}

resource "azurerm_private_dns_zone" "blob" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = azurerm_resource_group.prod_rg.name
}

resource "azurerm_private_dns_zone" "dfs" {
  name                = "privatelink.dfs.core.windows.net"
  resource_group_name = azurerm_resource_group.prod_rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "blob_link" {
  name                  = "blob-dns-vnet-link"
  resource_group_name   = azurerm_resource_group.prod_rg.name
  private_dns_zone_name = azurerm_private_dns_zone.blob.name
  virtual_network_id    = azurerm_virtual_network.prod_vnet.id
}

resource "azurerm_private_dns_zone_virtual_network_link" "dfs_link" {
  name                  = "dfs-dns-vnet-link"
  resource_group_name   = azurerm_resource_group.prod_rg.name
  private_dns_zone_name = azurerm_private_dns_zone.dfs.name
  virtual_network_id    = azurerm_virtual_network.prod_vnet.id
}

resource "azurerm_private_endpoint" "adls_blob" {
  name                = "pe-stvoltsentinelprod-blob"
  location            = azurerm_resource_group.prod_rg.location
  resource_group_name = azurerm_resource_group.prod_rg.name
  subnet_id           = azurerm_subnet.private_endpoint_subnet.id

  private_service_connection {
    name                           = "psc-stvoltsentinelprod-blob"
    private_connection_resource_id = azurerm_storage_account.prod_adls.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "blob-dns-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.blob.id]
  }
}

resource "azurerm_private_endpoint" "adls_dfs" {
  name                = "pe-stvoltsentinelprod-dfs"
  location            = azurerm_resource_group.prod_rg.location
  resource_group_name = azurerm_resource_group.prod_rg.name
  subnet_id           = azurerm_subnet.private_endpoint_subnet.id

  private_service_connection {
    name                           = "psc-stvoltsentinelprod-dfs"
    private_connection_resource_id = azurerm_storage_account.prod_adls.id
    subresource_names              = ["dfs"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dfs-dns-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.dfs.id]
  }
}

# Enable after endpoint/DNS validation; otherwise Terraform and local dev access can be blocked.
resource "azurerm_storage_account_network_rules" "adls_network_rules" {
  storage_account_id         = azurerm_storage_account.prod_adls.id
  default_action             = "Deny"
  bypass                     = ["AzureServices", "Logging", "Metrics"]
  virtual_network_subnet_ids = [azurerm_subnet.storage_subnet.id]
}
