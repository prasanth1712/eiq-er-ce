ENROLL_SECRET=$( sed -n 's/ENROLL_SECRET=//p' .env | cut -d':' -f1)
cp nginx/certificate.crt resources/
cp nginx/certificate.crt resources/windows/x64/
cp nginx/certificate.crt resources/windows/x86/
cp nginx/certificate.crt resources/linux/x64/
echo $ENROLL_SECRET>resources/secret.txt
echo $ENROLL_SECRET>resources/windows/x64/secret.txt
echo $ENROLL_SECRET>resources/windows/x86/secret.txt
echo $ENROLL_SECRET>resources/linux/x64/secret.txt
echo $ENROLL_SECRET>resources/darwin/secret.txt

