#!/bin/bash

# Set the date format
date_format="%Y_%m_%d"

# Get today's and yesterday's date
today=$(date +$date_format)
yesterday=$(date -d "tomorrow" +$date_format)
twodaysago=$(date -d "yesterday" +$date_format)

echo "${today}"
echo "${yesterday}"
echo "${twodaysago}"
rm -Rf ~/Downloads/tonightsvotes/
rm ~/Downloads/tonightsvotes.zip
mkdir ~/Downloads/tonightsvotes/
mkdir ~/Downloads/tonightsvotes/raw/
mkdir ~/Downloads/tonightsvotes/summary/


aws s3 cp s3://qcb2-dashboard-data-store/summaryvotelog/ ~/Downloads/tonightsvotes/summary/  --recursive --exclude "*" --include "${today}*" --include "${yesterday}*" --include "${twodaysago}*"
aws s3 cp s3://qcb2-dashboard-data-store/rawvotelog/ ~/Downloads/tonightsvotes/raw/ --recursive --exclude "*" --include "${today}*" --include "${yesterday}*" --include "${twodaysago}*"
cat ~/Downloads/tonightsvotes/summary/*.txt > ~/Downloads/tonightsvotes/combined_output.txt
zip -r ~/Downloads/tonightsvotes.zip ~/Downloads/tonightsvotes/
