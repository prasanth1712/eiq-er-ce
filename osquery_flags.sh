touch "$(dirname "$(pwd)")"/.rnd
a=$1
echo $a
for i in $(find $PWD -type  f -name \*.flags); do # Not recommended, will break on whitespace
    sed  's/tls_hostname=.*/tls_hostname='"$a"'/g' $i > "${1}_copy"
    rm -rf $i
    mv "${1}_copy" $i
done
rm -rf "$(dirname "$(pwd)")"/.rnd
