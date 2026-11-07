zcat -f /workspace/logs/access.log* | awk '{print $9}' | grep -c '^5'
