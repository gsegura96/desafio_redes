#!/bin/bash

if [ $# != 2 ]; then
    echo "Usage: $0 <total_requests> <domain>"
    exit 1
fi

total_requests=$1
request_domain=$2

request_types=(A TXT ANY)
# request_types=(A AAAA CNAME MX NS PTR TXT)

for request_type in "${request_types[@]}"; 
do
    mkdir -p results/$request_domain/$request_type  
done


providers=(custom google cloudflare opendns norton comodo )
declare -A ip=(
    [custom]="35.232.39.227"
    [google]="8.8.8.8"
    [cloudflare]="1.1.1.1"
    [opendns]="208.67.222.222"
    [norton]="199.85.126.10"
    [comodo]="8.26.56.26"
)


echo $total_requests "requests"
for request_type in "${request_types[@]}"; 
do
    echo "###############################################"
    echo "Testing $request_type"
    echo "###############################################"
    for provider in "${providers[@]}"; do
        echo "$provider ip: ${ip[$provider]}"
        > results/$request_domain/$request_type/${provider}.txt
        > results/$request_domain/$request_type/${provider}_response.txt
        dig +time=5 @"${ip[$provider]}" $request_domain $request_type >> results/$request_domain/$request_type/${provider}_response.txt
        echo 0
        for i in $(seq 0 $total_requests)
            do
            echo -e '\e[1A\e[K' $i
            dig +time=5 @"${ip[$provider]}" $request_domain $request_type | grep "Query time" | awk '{print $4}' >> results/$request_domain/$request_type/${provider}.txt
        done
    done
done

echo "###############################################"
echo "processing results"
echo "###############################################"
> results/$request_domain/results.csv
echo "request domain: ${request_domain}" >> results/$request_domain/results.csv
echo "total requests: ${total_requests}" >> results/$request_domain/results.csv

for request_type in "${request_types[@]}"; 
do
    echo "" >> results/$request_domain/results.csv
    echo $request_type >> results/$request_domain/results.csv
    echo "provider; min; max; mean; median" >> results/$request_domain/results.csv

    for provider in "${providers[@]}"; do
        max=$(cat results/$request_domain/$request_type/${provider}.txt | sort -n | tail -1)
        min=$(cat results/$request_domain/$request_type/${provider}.txt | sort -n | head -1)
        mean=$(cat results/$request_domain/$request_type/${provider}.txt | awk '{sum+=$1} END {print sum/NR}')
        median=0
        if [ $(cat results/$request_domain/$request_type/${provider}.txt | wc -l) -gt 1 ]; then
            median=$(cat results/$request_domain/$request_type/${provider}.txt | sort -n | awk '{a[NR]=$1} END {print a[int(NR/2)]}')
        fi
        echo "$provider; $min; $max; $mean; $median" >> results/$request_domain/results.csv
    done
done


