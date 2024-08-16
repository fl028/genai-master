CREATE DATABASE IF NOT EXISTS `data` 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `data`;

-- Create the `tickets` table
DROP TABLE IF EXISTS `tickets`;
CREATE TABLE `tickets` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `sap_ticketstatus` VARCHAR(50) DEFAULT NULL,
  `sap_ticketstatus_t` VARCHAR(50) DEFAULT NULL,
  `sap_ticketno` VARCHAR(50) DEFAULT NULL,
  `cdl_text` VARCHAR(250) DEFAULT NULL,
  `guid` VARCHAR(50) DEFAULT NULL,
  `processtype` VARCHAR(50) DEFAULT NULL,
  `action` VARCHAR(50) DEFAULT NULL,
  `company` INT DEFAULT NULL,
  `reporter` INT DEFAULT NULL,
  `supportteam` INT DEFAULT NULL,
  `editor` INT DEFAULT NULL,
  `status` VARCHAR(50) DEFAULT NULL,
  `statustxt` VARCHAR(50) DEFAULT NULL,
  `category` VARCHAR(50) DEFAULT NULL,
  `component` VARCHAR(50) DEFAULT NULL,
  `ibase` INT DEFAULT NULL,
  `sysrole` VARCHAR(10) DEFAULT NULL,
  `priority` INT DEFAULT NULL,
  `title` VARCHAR(255) DEFAULT NULL,
  `text` MEDIUMTEXT DEFAULT NULL,
  `text2` VARCHAR(50) DEFAULT NULL,
  `security` VARCHAR(50) DEFAULT NULL,
  `postpuntil` VARCHAR(50) DEFAULT NULL,
  `linkid` VARCHAR(50) DEFAULT NULL,
  `cdlid` VARCHAR(50) DEFAULT NULL,
  `optid` VARCHAR(50) DEFAULT NULL,
  `psp` VARCHAR(50) DEFAULT NULL,
  `units` VARCHAR(50) DEFAULT NULL,
  `type` VARCHAR(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- Create the `tickets_texts` table
DROP TABLE IF EXISTS `tickets_texts`;
CREATE TABLE `tickets_texts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `text` MEDIUMTEXT DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- Create the `tickets_summary` table
DROP TABLE IF EXISTS `tickets_summary`;
CREATE TABLE `tickets_summary` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `question` TEXT DEFAULT NULL,
  `answer` TEXT DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- Create the `tickets_texts_cleaned` table
DROP TABLE IF EXISTS `tickets_texts_cleaned`;
CREATE TABLE `tickets_texts_cleaned` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `text` MEDIUMTEXT DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;
