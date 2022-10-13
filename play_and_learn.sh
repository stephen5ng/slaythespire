#!/bin/bash -e
TRIALS=200
TIME_SECONDS=600

rm -f training.log
rm -f sts.csv
python sts.py "IRONCLAD_STARTER" --trials=$TRIALS --turns=40 --monster=JawWorm --strategy=RandomPlayer  --seed=$SECONDS
mv sts.csv sts.random.csv; python fastai_sts.py sts.random.csv

echo "Playing AI 1"
python sts.py "IRONCLAD_STARTER" --trials=$TRIALS --turns=40 --monster=JawWorm --strategy=AIPlayer --seed=$SECONDS
(cat sts.random.csv; tail -n +2 sts.csv) > sts.ai_training.csv

end=$((SECONDS+$TIME_SECONDS))

while [ $SECONDS -lt $end ]; do
echo "Playing AI incremental"
wc -l sts.ai_training.csv
time python fastai_sts.py sts.ai_training.csv
rm -f sts.csv
time python sts.py "IRONCLAD_STARTER" --trials=$TRIALS --turns=40 --monster=JawWorm --strategy=AIPlayer  --seed=$SECONDS > hp.txt
echo $(date +%H:%M:%S), $(cat hp.txt) >> training.log
cat hp.txt
cp sts.ai_training.csv sts.tmp.csv
tail -n +2 sts.csv >> sts.tmp.csv
mv sts.tmp.csv sts.ai_training.csv

done

gnuplot sts.gplot