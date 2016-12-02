#!/bin/bash
set -eu

wget --no-check-certificate -O AppCAG3Root.cer https://www.lgpki.jp/CAInfo/AppCAG3Root.cer
A=$(openssl x509 -noout -in AppCAG3Root.cer -inform DER -fingerprint)
B="SHA1 Fingerprint=6F:38:84:56:8E:99:C8:C6:AC:0E:5D:DE:2D:B2:02:DD:00:2E:36:63"
if [ "${A,,}" != "${B,,}" ]; then
	echo "Bad certificate AppCAG3Root.cer" >&2
	exit -1
fi
wget --no-check-certificate -O AppCAG3Sub1.cer https://www.lgpki.jp/CAInfo/AppCAG3Sub1.cer
A=$(openssl x509 -noout -in AppCAG3Sub1.cer -inform DER -fingerprint)
B="SHA1 Fingerprint=D2:0C:A4:B2:A6:A6:81:A8:B0:2A:68:93:38:E0:FC:BB:DA:6A:E7:F5"
if [ "${A,,}" != "${B,,}" ]; then
	echo "Bad certificate AppCAG3Sub1.cer" >&2
	exit -1
fi

rm -f lgpki.pem
openssl x509 -in AppCAG3Root.cer -inform DER >> lgpki.pem
openssl x509 -in AppCAG3Sub1.cer -inform DER >> lgpki.pem
