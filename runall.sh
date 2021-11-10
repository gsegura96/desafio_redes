total_requests=200


echo "#################### redesce ####################"
rm -rf results/redesce.com/*
./testdns.sh $total_requests redesce.com

echo "#################### google ####################"
rm -rf results/google.com/*
./testdns.sh $total_requests google.com


echo "#################### tecdigital ####################"
rm -rf results/tecdigital.tec.ac.cr/*
./testdns.sh $total_requests tecdigital.tec.ac.cr