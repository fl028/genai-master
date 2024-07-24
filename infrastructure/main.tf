resource "random_pet" "rg_name" {
  prefix = var.resource_group_name_prefix
}

resource "azurerm_resource_group" "rg" {
  location = var.resource_group_location
  name     = random_pet.rg_name.id
}

# Create virtual network
resource "azurerm_virtual_network" "default" {
  name                = "Vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# Create a subnet for the VM
resource "azurerm_subnet" "vm_subnet" {
  name                 = "Subnet-VM"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.default.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Manages the Subnet
resource "azurerm_subnet" "db_subnet" {
  address_prefixes     = ["10.0.2.0/24"]
  name                 = "Subnet-DB"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.default.name
  service_endpoints    = ["Microsoft.Storage"]

  delegation {
    name = "fs"

    service_delegation {
      name = "Microsoft.DBforMySQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# Enables you to manage Private DNS zones within Azure DNS
resource "azurerm_private_dns_zone" "default" {
  name                = "my.mysql.database.azure.com"
  resource_group_name = azurerm_resource_group.rg.name
}

# Enables you to manage Private DNS zone Virtual Network Links
resource "azurerm_private_dns_zone_virtual_network_link" "default" {
  name                  = "my.mysql.database.azure.com"
  private_dns_zone_name = azurerm_private_dns_zone.default.name
  resource_group_name   = azurerm_resource_group.rg.name
  virtual_network_id    = azurerm_virtual_network.default.id

  depends_on = [azurerm_subnet.db_subnet]
}

# Create public IP
resource "azurerm_public_ip" "public_ip" {
  name                = "PublicIP"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  allocation_method   = "Dynamic"
}

# Create Network Security Group and rule
resource "azurerm_network_security_group" "default" {
  name                = "NetworkSecurityGroup"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# Associate public IP with network interface of virtual machine
resource "azurerm_network_interface" "nic1" {
  name                = "NIC1"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  ip_configuration {
    name                          = "nic_configuration1"
    subnet_id                     = azurerm_subnet.vm_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.public_ip.id
  }
}

# Generate random text for unique storage account name
resource "random_id" "random_id" {
  keepers = {
    resource_group = azurerm_resource_group.rg.name
  }
  byte_length = 8
}

# Create storage account for boot diagnostics
resource "azurerm_storage_account" "storage_account" {
  name                    = "diag${random_id.random_id.hex}"
  location                = azurerm_resource_group.rg.location
  resource_group_name     = azurerm_resource_group.rg.name
  account_tier            = "Standard"
  account_replication_type = "LRS"
}

# creating cloud init script
data "template_cloudinit_config" "vm" {
  gzip          = true
  base64_encode = true

  part {
    content_type = "text/cloud-config"
    content = <<EOF
    package_update: true
    package_upgrade: true
    packages:
      - docker.io
      - mysql-client
      - python3.10-venv
    EOF
  }

  part {
    content_type = "text/cloud-config"
    content = <<EOF
    runcmd:
      - date +"%T.%N"
      - echo "Start cloud init"
      - usermod -aG docker azureadmin
    EOF
  }
}

resource "azurerm_linux_virtual_machine" "vm1" {
  name                   = "vm1"
  location               = azurerm_resource_group.rg.location
  resource_group_name    = azurerm_resource_group.rg.name
  network_interface_ids  = [azurerm_network_interface.nic1.id] 
  size                   = "Standard_B2s"          

  custom_data = data.template_cloudinit_config.vm.rendered 

  computer_name  = "vm1"
  admin_username = var.username

  os_disk {
    name                 = "osdisk1"
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  source_image_reference {
    publisher = "canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  admin_ssh_key {
    username   = var.username
    public_key = azapi_resource_action.ssh_public_key_gen.output.publicKey
  }

  boot_diagnostics {
    storage_account_uri = azurerm_storage_account.storage_account.primary_blob_endpoint  # Use the storage account for the first VM
  }
}

# Generate random value for the MySQL server password
resource "random_password" "mysql_password" {
  length           = 32
  lower            = true
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
  numeric          = true
  override_special = "_"
  special          = true
  upper            = true
}

# Create MySQL Flexible Server
resource "azurerm_mysql_flexible_server" "mysql" {
  name                         = "genai-master-db"
  location                     = azurerm_resource_group.rg.location
  resource_group_name          = azurerm_resource_group.rg.name
  administrator_login          = "mysqladmin"
  administrator_password       = random_password.mysql_password.result
  backup_retention_days        = 1
  geo_redundant_backup_enabled = false
  sku_name                     = "B_Standard_B1s"
  version                      = "8.0.21"
  private_dns_zone_id          = azurerm_private_dns_zone.default.id
  delegated_subnet_id          = azurerm_subnet.db_subnet.id
  zone = 1

  storage {
    size_gb = 20
  }
}

output "mysql_password" {
  value = random_password.mysql_password.result
  sensitive = true
}

output "public_ip_address" {
  value = azurerm_linux_virtual_machine.vm1.public_ip_address
}

data "template_file" "ssh_config" {
  template = <<-EOF
    Host vm1
        HostName ${azurerm_linux_virtual_machine.vm1.public_ip_address}
        User azureadmin
        Port 22
        IdentityFile ${var.PROJECT_ROOT_PATH}\\infrastructure\\${var.private_key_filename}
  EOF
}

resource "local_file" "vscode_ssh_config" {
  filename = "vscode_ssh_config"
  content  = data.template_file.ssh_config.rendered

  depends_on = [azurerm_linux_virtual_machine.vm1]
}
