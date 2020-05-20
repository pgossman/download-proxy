server="10.1.10.10"
server_user="root"
server_path="/var/www/vpn-app"

echo "Copying files..."
scp -r ./* ${server_user}@${server}:${server_path} > /dev/null
ssh ${server_user}@${server} \
    "find ${server_path} -type f -exec chmod 0644 {} \; ;\
    find ${server_path} -type d -exec chmod 0755 {} \; ;\
    chmod 0755 ${server_path}/{run,wsgi}.py; \
    chmod 0755 ${server_path}/src/test.sh"

echo "Restarting apache..."
ssh ${server_user}@${server} "systemctl restart httpd"
