<?xml version="1.0"?>
<installation>
    <primary-disk>sda</primary-disk>
    <keymap>us</keymap>
    <root-password>CHANGE_ME_TO_SOMETHING_APPROPRIATE</root-password>
    <source type="url">http://$server/cblr/links/$distro</source>
    <post-install-script type="url">
        http://$server/cblr/aux/xenserver/post-install
    </post-install-script>
    <admin-interface name="eth0" proto="dhcp" />
    <timezone>UTC</timezone>
    <hostname>$hostname</hostname>
</installation>

