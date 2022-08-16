#!/bin/bash

echo Slay the Spire simulation
echo

# echo "<pre>"
prefix="https://htmlpreview.github.io/?https://raw.githubusercontent.com/stephen5ng/slaythespire/main/charts/"
cd charts
for filename in *; do
    echo "<a href=\"$prefix$filename\">${filename/.html/}</a>"
    echo
    echo
done

# echo "</pre>"