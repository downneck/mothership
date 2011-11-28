class openssh::server {

    include openssh::client

	case $architecture {
		"x86_64": {
    			package { "openssh-server":
        		ensure => "5.5p1-21.x86_64",
    			}
		}

		"i386": {
    			package { "openssh-server":
        		ensure => "5.5p1-21.i386",
    			}
		}
	}
}
