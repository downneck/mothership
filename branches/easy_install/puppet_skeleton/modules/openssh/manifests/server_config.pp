class openssh::server_config {

    include openssh::server

    File {
        require => Class["openssh::server"],
        owner => root,
        group => root,
        mode => 644,
        ensure => present,
    }


    $sshd_config = "/etc/ssh/sshd_config"
    $sshd_config_template = "openssh/sshd_config.erb"

   concat { "${sshd_config}":
        mode  => 0600,
        owner => root,
        group => root,
    }

    concat::fragment { "sshd_config_head":
        order => 10,
        content => template($sshd_config_template),
        target => $sshd_config,
    }

    $ssh_config = "/etc/ssh/ssh_config"
    file { $ssh_config:
        source  => "puppet:///modules/openssh${ssh_config}",
    }
  
}
