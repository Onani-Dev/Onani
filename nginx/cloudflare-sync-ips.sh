#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-05-15 06:44:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-15 07:25:27

CLOUDFLARE_FILE_PATH=${1:-/etc/nginx/cloudflare}

echo "#Cloudflare" > $CLOUDFLARE_FILE_PATH;
echo "" >> $CLOUDFLARE_FILE_PATH;

echo "# - IPv4" >> $CLOUDFLARE_FILE_PATH;
for i in `curl -s -L https://www.cloudflare.com/ips-v4`; do
        echo "set_real_ip_from $i;" >> $CLOUDFLARE_FILE_PATH;
done

echo "" >> $CLOUDFLARE_FILE_PATH;
echo "# - IPv6" >> $CLOUDFLARE_FILE_PATH;
for i in `curl -s -L https://www.cloudflare.com/ips-v6`; do
        echo "set_real_ip_from $i;" >> $CLOUDFLARE_FILE_PATH;
done

echo "" >> $CLOUDFLARE_FILE_PATH;
echo "real_ip_header X-Forwarded-For;" >> $CLOUDFLARE_FILE_PATH;

#test configuration and reload nginx
# nginx -t && rc-service nginx restart
