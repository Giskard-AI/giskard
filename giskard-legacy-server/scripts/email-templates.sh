#!/usr/bin/env bash
set -e

# Generate email templates from MJML
echo "Generating email templates from MJML..."
cd "/app/app/email-templates/"
mkdir -p "build"
cd "src"
for fi in *.mjml
do
    fo=${fi%.mjml}.html
    mjml $fi -o ../build/$fo
done
cd ..
chmod -R a+w "build"
echo "Done"