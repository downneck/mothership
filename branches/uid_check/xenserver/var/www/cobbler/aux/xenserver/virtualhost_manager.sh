#!/bin/bash
#
# Author: ikenticus
#
# CLI script to create and destroy a Citrix Xen VM with as few parameters as possible
# Notes:  Place this script on a xenserver


SELF=${0##*/}

# Global settings (gilt)
TPL="CentOS 5.4 (64-bit)" 


# Default VM settings
CPU=1
MEM=1024            # MB: Memory
VDI=8               # GB: Virtual Disk
NIC=0               # xenbr# to kick from
STORAGE="storage"   # Storage Repository to use
ASK="YES"           # Ask before destroying a VM


usage() {
    cat << EOF
Usage: $SELF -x

Destroy a VM:
    $SELF -x vmtest1

Create a default VM, specify mac address:
    $SELF -S 10.10.10.10 -D centos55 -c vmtest2 -m 00:11:22:33:44:55

Create VM with multiple mac/interfaces defined:
    $SELF -S 10.10.10.10 -D centos55 -c vmtest3 -m xenbr0=00:11:22:33:44:55,bond0=66:77:88:99:AA:BB

Kickstart VM on eth1 with 2 CPUs, 16GB disk and 2GB memory
    $SELF -S 10.10.10.10 -D centos55 -c vmtest4 -m 00:11:22:33:44:55 -N1 -M2048 -V16 -C2

Other Switches:
    -h          Help, this usage screen
    -l          List all VMs on the server
    -x name     Destroy existing VM with name
    -c name     Create new VM with name
    -m hwaddr   MAC Address used to create new VM
    -s name     Storage Repository to use (default: "$STORAGE")
    -D distro	Distro name to use for kickstart
    -T tpl      Template to clone (default: "$TPL")
    -C #        CPU, for new VM (default: $CPU)
    -M MB       Memory, in MB, for new VM (default: $MEM)
    -N #        Interface for eth->xenbr in new VM (default: $NIC)
    -V GB       Virtual Disk, in GB, for new VM (default: $VDI)
    -d          Don't ask before destroying a VM
EOF
    exit 3
}


destroy_vm() {
    local vm_name=$1
    local vm_uuid=$(xe vm-list name-label=$vm_name | grep ^uuid | awk '{ print $NF }')
    local vdi_uuid=$(xe vbd-list vm-uuid=$vm_uuid | grep vdi-uuid | awk '{ print $NF }')

    if [[ -z $vm_uuid ]]; then
        echo "Cannot destroy $vm_name as it does not exist"
        exit 0
    fi
    xe vm-list uuid=$vm_uuid
    xe vdi-list uuid=$vdi_uuid
    if [[ $ASK == 'NO' ]]; then
        ans='yes'
    else
        read -p "Are you sure you want to shutdown and destroy $vm_name? (yes/no) " ans
    fi
    if [[ $ans == 'yes' ]]; then
        echo "Shutting Down VM: $vm_uuid"
          xe vm-shutdown uuid=$vm_uuid
        echo "Destroying VM: $vm_uuid"
          xe vm-destroy uuid=$vm_uuid
        echo "Destroying VDI: $vdi_uuid"
          xe vdi-destroy uuid=$vdi_uuid
        exit 0
    else
        echo "Destruction of $vm_name aborted!"
        exit 1
    fi
}


virtual_nic() {
    local vm=$1     ; shift
    local num=$1    ; shift
    local nic=$1    ; shift
    local mac=$1

    if [[ -z ${nic##bond*} ]]; then
        nicname=$nic
        nic=$(xe network-list name-label=$nicname params=bridge | awk '{ print $NF }')
        if [[ -z $nic ]]; then
            bondname=$(xe pif-list device=$nicname params=network-name-label 2>/dev/null|head -1|sed 's/^.*: //')
            nic=$(xe network-list name-label="$bondname" params=bridge | awk '{ print $NF }')
        fi
    fi

    if [[ -z $(xe network-list bridge=$nic) ]]; then
        echo "Network Bridge $nic does not exist, skipping"
        return
    fi
    echo "Acquiring nic uuid for $nic"
      net_uuid=$(xe network-list bridge=$nic | grep ^uuid | awk '{ print $NF }')
    echo "Attaching interface $num to VM using mac=$mac"
      vif_uuid=$(xe vif-create vm-uuid=$vm network-uuid=$net_uuid device=$num mac=$mac)
}


create_vm() {
    local vm_name=$1        ; shift
    local net_num=$1        ; shift
    local cpu_num=$1        ; shift
    local mem_num=$1        ; shift
    local vdi_num=$1        ; shift
    local mac=$1            ; shift
    local storage=${1//__/ }; shift
    local template=$*

    if [[ -n $(xe vm-list name-label=$vm_name) ]]; then
        echo "Cannot create VM $vm_name as it already exists"
        exit 2
    fi

    echo "Acquiring SR uuid for $storage"
    [[ -z ${storage//*Local*} ]] && sr_opts="host=$HOSTNAME"
    sr_uuid=$(xe sr-list name-label="$storage" $sr_opts|grep ^uuid|awk '{ print $NF }')
    if [[ -z $sr_uuid ]]; then
        # attempt wildcard match
        sr_name=$(xe sr-list|grep $storage $sr_opts|grep -v Removable|head -1|sed 's/^.*: //')
        sr_uuid=$(xe sr-list name-label="$sr_name"|grep ^uuid|awk '{ print $NF }')
    fi
    if [[ -z $sr_uuid ]]; then
        echo "Cannot determine storage repository to use"
        exit 4
    fi

    echo "Creating VM: $vm_name"
        vm_uuid=$(xe vm-install new-name-label=$vm_name template="$template" sr-uuid=$sr_uuid)
    echo "Resizing VDI to $vdi_num GB"
        vdi_uuid=$(xe vbd-list vm-uuid=$vm_uuid | grep vdi-uuid | awk '{ print $NF }')
        xe vdi-resize uuid=$vdi_uuid disk-size=$[vdi_num*1024*1024*1024]
    echo "Resizing Memory to $mem_num MB"
        mmin=$[1024*1024*512]
        mmax=$[1024*1024*mem_num]
        xe vm-memory-limits-set vm=$vm_uuid static-min=$mmin static-max=$mmax dynamic-min=$mmax dynamic-max=$mmax
    echo "Resizing VCPU to $cpu_num"
        xe vm-param-set uuid=$vm_uuid VCPUs-max=$cpu_num
        xe vm-param-set uuid=$vm_uuid VCPUs-at-startup=$cpu_num

    cnt=0
    if [[ -z ${mac//*=*} ]]; then
        IFS=,; set -- $mac; unset IFS
        for pair in $*; do
            IFS==; set -- $pair; unset IFS
            virtual_nic $vm_uuid $cnt $1 $2
            cnt=$[cnt+1]
        done
    else
        virtual_nic $vm_uuid $num xenbr$net_num $mac
    fi

    echo "Setting network install location for VM"
      xe vm-param-set uuid=$vm_uuid other-config:install-repository="$REPO"
    echo "Setting kickstart parameters for VM"
      xe vm-param-set uuid=$vm_uuid PV-args="ks=$KICK/$vm_name ksdevice=eth$net_num noipv6 utf8"
    echo "Starting $vm_name VM: $vm_uuid"
      xe vm-start uuid=$vm_uuid
}


list_vm() {
    xe vm-list | grep name-label | grep -v ^Control | awk '{ print $NF }'
    exit 0
}


if [[ -z $( which xe ) ]]; then
    echo "XenAPI does not appear to be on this host!"
    usage
fi
while getopts "hlx:c:m:s:S:D:T:C:M:N:G:V:d" opt; do
    case $opt in
        h)  usage       ;;
        l)  list_vm     ;;
        t)  TPL=$OPTARG ;;
        s)  STORAGE=$OPTARG ;;
        S)  SERVER=$OPTARG ;;
        D)  DISTRO=$OPTARG ;;
        C)  CPU=$OPTARG ;;
        M)  MEM=$OPTARG ;;
        N)  NIC=$OPTARG ;;
        V)  VDI=$OPTARG ;;
        m)  MAC=$OPTARG ;;
        c)  VM=$OPTARG  ;;
        d)  ASK=NO ;;
        x)  destroy_vm $OPTARG ;;
        *)  echo "Invallid switch!"
            usage
            ;;
    esac
done
if [[ -z $SERVER || -z $DISTRO ]]; then
    echo "Missing Server or Distro settings!"
    usage
fi
REPO=http://$SERVER/cblr/links/$DISTRO/
KICK=http://$SERVER/cblr/svc/op/ks/system
if [[ -n $VM ]]; then
    if [[ -z $MAC ]]; then
        echo "MAC Address not specified!"
        usage
    else
        create_vm $VM $NIC $CPU $MEM $VDI $MAC ${STORAGE// /__} $TPL
        exit 0
    fi
fi
usage


