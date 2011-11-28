#!/bin/bash

libdir=/var/lib/cobbler
srcdir=/var/www/cobbler
dstdir=/tftpboot

for profile in $( grep -l xenserver.ks $libdir/config/profiles.d/* ); do
    json=${profile##*/}
    name=${json%-*.*}
    [[ -d $dstdir/images/$name ]] && \
    rsync -av $srcdir/ks_mirror/$name/{install.img,boot/vmlinuz} \
        $dstdir/images/$name/
done

for file in $( grep -l xen.gz /tftpboot/pxelinux.cfg/* ); do
    sed -i -e 's!initrd=\(/images/.*/\)\(xen.gz \)ks.*ks=\(.*\)$!\1\2dom0_mem=752M com1=115200,8n1 console=com1,vga --- \1vmlinuz xencons=hvc console=hvc0 console=tty0 answerfile=\3 install --- \1install.img!;' $file
done

