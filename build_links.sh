#!/bin/bash

echo Slay the Spire simulation
echo

# echo "<pre>"
prefix="https://htmlpreview.github.io/?https://raw.githubusercontent.com/stephen5ng/slaythespire/main/"
for filename in charts/*; do
    echo "<a target="_blank" href=\"$prefix$filename\">$filename</a>"
    echo
    echo
done

# echo "</pre>"