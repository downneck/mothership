define sudo::grant(
        $users    = ['ALL'],
        $hosts    = 'ALL',
        $commands = 'ALL',
        $runas    = 'ALL') {
    concat::fragment { "sudoers ${name} grant":
        content => template('sudo/sudoers.erb'),
        order   => 99,
        target  => $sudo::sudoers_file,
    }
}
