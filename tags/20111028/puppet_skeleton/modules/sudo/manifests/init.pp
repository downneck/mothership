class sudo {
    $sudoers_path = "/etc"
    $sudoers_file = "${sudoers_path}/sudoers"
    $sudoers_local_file = "${sudoers_path}/sudoers.local"

    concat { "${sudoers_file}":
        mode  => 0440,
        owner => root,
        group => root,
    }

    concat::fragment { "sudoers_header":
        # Start from 10 as sort order
        order  => 10,
        source  => "puppet:///modules/sudo/sudoers.header",
        target => $sudoers_file,
    }

    concat::fragment { "sudoers_sysadmin":
        ensure  => present,
        order   => 20,
        source  => "puppet:///modules/sudo/sudoers.sysadmin",
        target  => $sudoers_file,
    }

    concat::fragment { "sudoers_local":
        order   => 50,
        ensure  => "${sudoers_path}/sudoers.local",
        mode    => 0440,
        target  => $sudoers_file,
    }
}
