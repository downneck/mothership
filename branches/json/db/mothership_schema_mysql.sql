-- MySQL dump 10.13  Distrib 5.1.54, for debian-linux-gnu (i686)
--

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `application_instances`
--

DROP TABLE IF EXISTS `application_instances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `application_instances` (
  `ip` char(15) DEFAULT NULL,
  `port` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `tag` varchar(100) DEFAULT NULL,
  `started_at` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `scms_version_id` int(11) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dns_addendum`
--

DROP TABLE IF EXISTS `dns_addendum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dns_addendum` (
  `realm` varchar(10) DEFAULT NULL,
  `site_id` varchar(3) DEFAULT NULL,
  `host` varchar(100) DEFAULT NULL,
  `target` varchar(200) DEFAULT NULL,
  `record_type` varchar(10) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `description` varchar(150) DEFAULT NULL,
  `sudo_cmds` varchar(2000) DEFAULT NULL,
  `groupname` varchar(64) NOT NULL,
  `site_id` varchar(3) NOT NULL,
  `realm` varchar(10) NOT NULL,
  `gid` int(11) NOT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`groupname`,`realm`,`site_id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hardware`
--

DROP TABLE IF EXISTS `hardware`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `hardware` (
  `hw_tag` varchar(200) NOT NULL,
  `purchase_date` date DEFAULT NULL,
  `manufacturer` varchar(100) DEFAULT NULL,
  `cores` int(11) DEFAULT NULL,
  `ram` int(11) DEFAULT NULL,
  `disk` varchar(100) DEFAULT NULL,
  `site_id` varchar(3) DEFAULT NULL,
  `cost` int(11) DEFAULT NULL,
  `kvm_switch` varchar(20) DEFAULT NULL,
  `kvm_port` smallint(6) DEFAULT NULL,
  `power_port` smallint(6) DEFAULT NULL,
  `power_switch` varchar(20) DEFAULT NULL,
  `model` varchar(200) DEFAULT NULL,
  `cpu_sockets` smallint(6) DEFAULT NULL,
  `cpu_speed` varchar(20) DEFAULT NULL,
  `rma` tinyint(1) NOT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  UNIQUE KEY `id` (`id`),
  PRIMARY KEY (`hw_tag`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kv`
--

DROP TABLE IF EXISTS `kv`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kv` (
  `key` varchar(100) DEFAULT NULL,
  `value` varchar(200) DEFAULT NULL,
  `hostname` varchar(200) DEFAULT NULL,
  `site_id` varchar(3) DEFAULT NULL,
  `realm` varchar(10) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `network`
--

DROP TABLE IF EXISTS `network`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `network` (
  `mac` varchar(17) DEFAULT NULL,
  `site_id` varchar(3) DEFAULT NULL,
  `realm` varchar(10) DEFAULT NULL,
  `vlan` int(11) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `netmask` varchar(15) DEFAULT NULL,
  `server_id` int(11) DEFAULT NULL,
  `interface` varchar(15) DEFAULT NULL,
  `switch` varchar(30) DEFAULT NULL,
  `switch_port` varchar(50) DEFAULT NULL,
  `ip` varchar(15) DEFAULT NULL,
  `bond_options` varchar(300) DEFAULT NULL,
  `hw_tag` varchar(200) DEFAULT NULL,
  `static_route` varchar(15) DEFAULT NULL,
  `public_ip` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tags`
--

DROP TABLE IF EXISTS `tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tags` (
  `name` varchar(50) DEFAULT NULL,
  `start_port` int(11) DEFAULT NULL,
  `stop_port` int(11) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `security_level` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `server_graveyard`
--

DROP TABLE IF EXISTS `server_graveyard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `server_graveyard` (
  `hostname` varchar(200) DEFAULT NULL,
  `site_id` varchar(3) DEFAULT NULL,
  `realm` varchar(10) DEFAULT NULL,
  `tag` varchar(20) DEFAULT NULL,
  `tag_index` smallint(6) DEFAULT NULL,
  `cores` smallint(6) DEFAULT NULL,
  `ram` int(11) DEFAULT NULL,
  `disk` int(11) DEFAULT NULL,
  `hw_tag` varchar(200) DEFAULT NULL,
  `os` varchar(15) DEFAULT NULL,
  `cobbler_profile` varchar(50) DEFAULT NULL,
  `comment` varchar(1000) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `provision_date` date DEFAULT NULL,
  `deprovision_date` date DEFAULT NULL,
  `virtual` tinyint(1) DEFAULT NULL,
  `security_level` smallint(6) DEFAULT NULL,
  `cost` int(11) DEFAULT NULL,
  `zabbix_template` varchar(300) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `servers`
--

DROP TABLE IF EXISTS `servers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `servers` (
  `hostname` varchar(200) DEFAULT NULL,
  `site_id` varchar(3) DEFAULT NULL,
  `realm` varchar(10) DEFAULT NULL,
  `tag` varchar(20) DEFAULT NULL,
  `tag_index` smallint(6) DEFAULT NULL,
  `cores` smallint(6) DEFAULT NULL,
  `ram` int(11) DEFAULT NULL,
  `disk` int(11) DEFAULT NULL,
  `hw_tag` varchar(200) DEFAULT NULL,
  `os` varchar(15) DEFAULT NULL,
  `cobbler_profile` varchar(50) DEFAULT NULL,
  `comment` varchar(1000) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `virtual` tinyint(1) DEFAULT NULL,
  `provision_date` date DEFAULT NULL,
  `security_level` smallint(6) DEFAULT NULL,
  `cost` int(11) DEFAULT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `zabbix_template` varchar(300) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `system_services`
--

DROP TABLE IF EXISTS `system_services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `system_services` (
  `name` varchar(200) DEFAULT NULL,
  `ip` varchar(15) DEFAULT NULL,
  `server_id` bigint(20) unsigned DEFAULT NULL,
  KEY `system_services_server_id_fkey` (`server_id`),
  CONSTRAINT `system_services_server_id_fkey` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_group_mapping`
--

DROP TABLE IF EXISTS `user_group_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_group_mapping` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `groups_id` bigint(20) unsigned DEFAULT NULL,
  `users_id` bigint(20) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `user_group_mapping_groups_id_fkey` (`groups_id`),
  KEY `user_group_mapping_users_id_fkey` (`users_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `ssh_public_key` varchar(1500) DEFAULT NULL,
  `username` varchar(64) NOT NULL,
  `site_id` varchar(3) NOT NULL,
  `realm` varchar(10) NOT NULL,
  `uid` int(11) NOT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `type` varchar(15) DEFAULT NULL,
  `hdir` varchar(100) DEFAULT NULL,
  `shell` varchar(100) DEFAULT NULL,
  `active` tinyint(1) DEFAULT '1',
  `email` varchar(100) DEFAULT NULL,
  UNIQUE KEY `id` (`id`),
  PRIMARY KEY (`username`,`realm`,`site_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `xen_pools`
--

DROP TABLE IF EXISTS `xen_pools`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `xen_pools` (
  `realm` varchar(10) DEFAULT NULL,
  `pool_id` smallint(6) DEFAULT NULL,
  `server_id` bigint(20) unsigned DEFAULT NULL,
  KEY `xen_pools_server_id_fkey` (`server_id`),
  CONSTRAINT `xen_pools_server_id_fkey` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `zeus_cluster`
--

DROP TABLE IF EXISTS `zeus_cluster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `zeus_cluster` (
  `cluster_name` varchar(50) DEFAULT NULL,
  `vhost` varchar(300) DEFAULT NULL,
  `ip` varchar(15) DEFAULT NULL,
  `public_ip` varchar(15) DEFAULT NULL,
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `port` int(11) DEFAULT NULL,
  `tg_name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-06-30 14:51:54
