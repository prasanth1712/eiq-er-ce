#!/bin/bash
ram=$(echo $(free -m | awk 'NR == 2 {printf($2)}'))
echo "RAM $ram"
multiplier=0.02
shm=$(echo $multiplier*$ram | bc -l)
shm=${shm%.*}
echo "SHARED MEMORY $shm"
sed -i 's/SHARED_MEMORY=.*/SHARED_MEMORY='"$shm"'m'/g .env
echo "Updated shared memory to env"
