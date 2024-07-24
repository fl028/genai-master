variable "resource_group_location" {
  default     = "westeurope"
  description = "Location of the resource group."
}

variable "resource_group_name_prefix" {
  type        = string
  default     = "rg"
  description = "Prefix of the resource group name that's combined with a random ID so name is unique in your Azure subscription."
}

variable "username" {
  type        = string
  description = "The username for the local account that will be created on the new VM."
  default     = "azureadmin"
}

variable "private_key_filename" {
  description = "Filename for the private key PEM file"
  type        = string
  default     = "private_key.pem"
}

variable "PROJECT_ROOT_PATH" {
  description = "Path to the project root directory"
  type        = string
  default     = "C:\\Users\\Florian\\Documents\\Development\\terraform\\infrastructure"
}