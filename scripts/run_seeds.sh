#!/bin/bash
# Seed study: same recipe (start = AitBAD kab.lstm, data = train_v4.list, 20k iterations),
# seed s = a different random order of the training list (Tesseract has no seed flag).
set -e
cd /home/claude/seeds
for s in 1 2 3; do
  python3 -c "import random;L=open('/home/claude/v3/train_v4.list').read().split();random.Random($s).shuffle(L);open('train_s$s.list','w').write('\n'.join(L)+'\n')"
  mkdir -p ck$s
  OMP_THREAD_LIMIT=1 lstmtraining --continue_from /home/claude/train/model/kab.lstm \
    --traineddata /home/claude/train/model/kab_start.traineddata \
    --train_listfile train_s$s.list --eval_listfile /home/claude/v3/val_same.list \
    --model_output ck$s/s$s --max_iterations 6000 > s$s.log 2>&1
  lstmtraining --stop_training --continue_from ck$s/s${s}_checkpoint \
    --traineddata /home/claude/train/model/kab_start.traineddata --model_output kabs$s.traineddata
  cp kabs$s.traineddata /home/claude/pilot/tessdata/
  cd /home/claude/ood; for set in set_bou set_bej set_liv set_aya; do python3 eval_lines.py $set kabs$s; done >> /home/claude/seeds/eval.log 2>&1; cd /home/claude/seeds
done
echo DONE >> eval.log
