#!/bin/bash
#
# Usage: mk_keys.sh [prefix]
#
# Makes two files: private_key.pem and certificate.pem, optionally prefixed
# with the first positional argument.
#
# Thanks to http://robinelvin.wordpress.com/2009/09/04/saml-with-django/

if [[ $# -ge 1 ]] ; then
	prefix="${1}-"
else
	prefix=""
fi
private_key="${prefix}private-key.pem"
certificate="${prefix}certificate.pem"

echo "** This utility will create the OpenSSL key and certificate for the keys app."
type -P openssl &>/dev/null || {
    echo "** This utility requires openssl but it's not installed.  Aborting." >&2;
    exit 1;
}

echo "** Starting OpenSSL Interaction ------------------------------------"
openssl genrsa > "${private_key}"
openssl req -new -x509 -key "${private_key}" -out "${certificate}" -days 365
echo "** Finished OpenSSL Interaction ------------------------------------"

echo "** These keys were created:"
ls -l -- "${private_key}" "${certificate}"
echo "** Finished."
