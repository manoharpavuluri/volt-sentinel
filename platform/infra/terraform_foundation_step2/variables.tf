variable "project_name" {
  type        = string
  description = "Short project name used in Azure resource names."
  default     = "voltsentinel"
}

variable "environment" {
  type        = string
  description = "Environment name."
  default     = "dev"
}

variable "location" {
  type        = string
  description = "Azure region."
  default     = "centralus"
}
