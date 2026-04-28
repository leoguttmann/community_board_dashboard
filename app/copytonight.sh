rm -Rf ~/Downloads/tonightsvotes/
rm ~/Downloads/tonightsvotes.zip
mkdir ~/Downloads/tonightsvotes/
mkdir ~/Downloads/tonightsvotes/raw/
mkdir ~/Downloads/tonightsvotes/summary/
aws s3 cp s3://cb7-dashboard-data-store/summaryvotelog/ ~/Downloads/tonightsvotes/summary/  --recursive --exclude "*" --include "2024_01_02*" --include "2024_01_03*"
aws s3 cp s3://cb7-dashboard-data-store/rawvotelog/ ~/Downloads/tonightsvotes/raw/ --recursive --exclude "*" --include "2024_01_02*" --include "2024_01_03*"
cat ~/Downloads/tonightsvotes/summary/*.txt > ~/Downloads/tonightsvotes/combined_output.txt
zip -r ~/Downloads/tonightsvotes.zip ~/Downloads/tonightsvotes/
