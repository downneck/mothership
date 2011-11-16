class openssh::services {

    $services = [ "sshd" ]
    service {
        $services:
            ensure => true,
            enable => true,
            hasrestart => true,
            hasstatus => true,
            require => Class['openssh::server'],
            subscribe => File["/etc/ssh/sshd_config"],
    }
}
