import sys; sys.path.insert(0,'/home/claude/91/outil'); sys.path.insert(0,'.')
from spacefix import build_lexicon, SpaceFixer
from kabocr_eval.metrics import count, rates, Counts
from kabocr_eval.charset import normalise
lex=build_lexicon(['train_gt_all.txt'])
val=[l.strip() for l in open('val_png.txt')]
hyp=open('val_v4.txt').read().split('\f')
gt=[open(p.replace('.png','.gt.txt')).read().strip() for p in val]
def score(fx):
    t=Counts()
    for g,h in zip(gt,hyp):
        h=h.strip(); h=fx.fix(h) if fx else h
        t=t+count(normalise(g,'lenient'),h)
    r=rates(t); return 100*r['CER'],100*r['WER']
print('base',score(None))
for mp in (2,3,4):
  for mf in (2,3,5,10):
    for mm in (2,3,5,10):
      print(mp,mf,mm,score(SpaceFixer(lex,mp,mf,mm)))
