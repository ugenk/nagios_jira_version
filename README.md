Jira version check scipt for icinga/nagios
==========================================

Script checks for latest version on atlassian website and against your server.

For now it supports:
- jira server/datacenter
- confluence
- jira service desk

Patches/mrs are welcome.

Installation on Debian/Ubuntu
-----------------------------

```commandline
apt -y install python3 git python3-requests python3-packaging python3-bs4
cp check_jira_version.py /usr/lib/nagios/plugins/
cp check-jira-version-command.conf /etc/icinga2/conf.d/check-jira-command.conf
```

Example configuration of icinga

```
apply Service "check_jira_version" {
  import "generic-service"
  check_command = "check_jira_version"
  assign where host.vars.jira_host
}

object Host "jira.example.com" {
  import "generic-host"
  address = "192.0.2.10"
  vars.jira_host = "jira.example.com"
  vars.jira_lts = true
}

object Host "wiki.example.com" {
  import "generic-host"
  address = "192.0.2.11"
  vars.jira_host = "wiki.example.com"
  vars.jira_software_type = "confluence"
  vars.jira_lts = true
}

object Host "sd.example.com" {
  import "generic-host"
  address = "192.0.2.12"
  vars.jira_host = "sd.example.com"
  vars.jira_software_type = "jira-service-desk"
  vars.jira_lts = false
}
```
