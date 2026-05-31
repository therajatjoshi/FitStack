output "resource_group_name" {
  description = "Name of the Azure resource group"
  value       = azurerm_resource_group.main.name
}

output "web_app_url" {
  description = "Default URL of the Linux Web App"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "acr_login_server" {
  description = "Login server for Azure Container Registry"
  value       = azurerm_container_registry.main.login_server
}
