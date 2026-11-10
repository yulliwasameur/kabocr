#!/bin/bash
# Learning curve: start from AitBAD, only n REAL lines (no synthetic, no augmentation), 4000 iterations, same seed order.
cd /home/claude/lc
for n in 500 2000 8000; do
  mkdir -p ck$n
  OMP_THREAD_LIMIT=1 lstmtraining --continue_from /home/claude/train/model/kab.lstm --traineddata /home/claude/train/model/kab_start.traineddata \
    --train_listfile real_$n.list --eval_listfile /home/claude/v3/val_same.list --model_output ck$n/lc --max_iterations 4000 > lc$n.log 2>&1
  lstmtraining --stop_training --continue_from ck$n/lc_checkpoint --traineddata /home/claude/train/model/kab_start.traineddata --model_output kablc$n.traineddata
  cp kablc$n.traineddata /home/claude/pilot/tessdata/
  cd /home/claude/ood; for s in set_bou set_bej set_liv; do python3 eval_lines.py $s kablc$n; done >> /home/claude/lc/eval.log 2>&1; cd /home/claude/lc
done
echo DONE >> eval.log
