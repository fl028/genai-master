# Configure the Azure provider
terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "3.112.0"
    }
    random = {
      source = "hashicorp/random"
      version = "3.6.2"
    }
    azapi = {
      source = "Azure/azapi"
      version = "1.14.0"
    }
     local = {
      source = "hashicorp/local"
      version = "2.5.1"
    }
  }

  required_version = ">= 1.1.0"
}

provider "azurerm" {
  features {}
}

provider "random" {
  # Configuration options
}

provider "azapi" {
  # Configuration options
}

provider "local" {
  # Configuration options
}