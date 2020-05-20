# Initialize a new system
# Targeted for CentOS, but can be adopted to other platforms

torrent_file_location=/srv/vpn-app/torrents

mkdir -p $torrent_file_location

# SELinux allows apache to write files to essential directories
semanage fcontext -a -t httpd_sys_rw_content_t $torrent_file_location
restorecon $torrent_file_location

# SELinux allows apache to make network connections
sesetbool -P httpd_can_network_connect 1
