#!/bin/bash
cd /home/sebastian/osint-web
git add -A
git commit -m "Auto-sync $(date '+%Y-%m-%d %H:%M')" --allow-empty
git push origin main >> /tmp/git-sync.log 2>&1
