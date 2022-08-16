#!/bin/bash

echo Slay the Spire simulation
echo

prefix="https://htmlpreview.github.io/?https://raw.githubusercontent.com/stephen5ng/slaythespire/main/"
for filename in charts/*; do
    echo "<a href=\"$prefix$filename\">$filename</a>"
done