# KabOCR-Bench — Guide d'annotation (version 1, 10/11/2026)

## À quoi sert ce travail

On veut un jeu de test **vérifié par un humain**, sur de **vrais scans**. C'est la seule façon de prouver que nos chiffres sont justes. Un relecteur de revue ne peut pas contester une vérité tapée et relue par des humains.

Chaque ligne est déjà **pré-remplie** par notre meilleur modèle. Ton travail : **corriger** ce texte pour qu'il soit exactement ce qui est imprimé.

## Règle d'or : transcription diplomatique

On tape **ce qui est imprimé, pas ce qui devrait l'être**.

- Une faute d'orthographe dans le livre ? On la **garde**.
- Un mot coupé en fin de ligne (« tamur- ») ? On garde le **tiret** et la coupure.
- Une lettre mal imprimée mais lisible ? On tape la lettre **voulue**.
- Une lettre vraiment illisible ? On tape **`#`** à sa place (une seule `#` par lettre).

## Les lettres kabyles

Utiliser **toujours** les lettres latines officielles, jamais leurs sosies.

| Lettre | Code | Ne pas confondre avec |
|---|---|---|
| ɛ Ɛ | U+025B, U+0190 | ε grec, ԑ cyrillique |
| ɣ Ɣ | U+0263, U+0194 | γ grec, ɤ |
| č ǧ | U+010D, U+01E7 | ğ (brève) |
| ḍ ḥ ṛ ṣ ṭ ẓ | point **dessous** | ḋ (point dessus) |
| ţ | t cédille U+0163 | ț (virgule dessous) |

L'outil a une **barre de lettres** : un clic insère la bonne lettre. Le logiciel d'évaluation ramène aussi automatiquement les sosies connus à la bonne lettre (mode « indulgent »), mais la vérité doit être propre.

**Si l'imprimé utilise un sosie** (par exemple un γ grec dans la police du livre), on tape la **lettre kabyle** (ɣ). On juge la forme, pas le code.

## Espaces et ponctuation

- On tape **un espace** entre deux mots, même si l'imprimé est serré ou étiré (texte justifié).
- Ponctuation : on suit **l'imprimé**. Si le livre met un espace avant « : », on le met.
- Guillemets : on garde la forme imprimée (« », “ ”, " ").

## Les boutons de statut

| Statut | Quand l'utiliser |
|---|---|
| **Corrigée** | Tu as vérifié la ligne ; le texte est maintenant exact (même si tu n'as rien changé) |
| **Hors périmètre** | La ligne est entièrement en **français**, en **arabe** ou en **tifinagh**, ou c'est un numéro de page seul |
| **Mauvaise découpe** | L'image ne contient pas une ligne entière (deux lignes collées, ligne coupée, image vide) |
| **Illisible** | Plus de la moitié de la ligne ne se lit pas |

Une ligne **mixte** (kabyle + quelques mots français) reste **dans le périmètre** : on tape tout, français compris.

## Contrôle qualité

1. **Deux annotateurs** pour 20 % des lignes (tirées au hasard par l'outil, marquées « double »). On mesure leur accord (CER entre les deux versions). Objectif : moins de 0,5 %.
2. Les désaccords sont **arbitrés** par une troisième personne.
3. **Partie cachée** : 50 % des lignes validées ne sont **jamais** montrées à quiconque développe les modèles. Elles servent une seule fois, pour le test final.

## Temps estimé

Environ **20 secondes par ligne** quand le modèle se trompe peu. 600 lignes ≈ **3 h 30** pour un annotateur.

## Ce qu'on ne fait pas

- On ne corrige **pas** l'orthographe de l'auteur.
- On ne **normalise pas** vers la graphie standard (ça viendra dans une couche séparée).
- On ne regarde **jamais** les sorties des autres systèmes pendant l'annotation (seulement le pré-remplissage du nôtre, ce qui est dit dans le papier).

**Biais connu et assumé** : partir de la sortie de notre modèle pourrait pousser l'annotateur à accepter ses erreurs. Contrôle : sur les lignes « double », le second annotateur part d'un champ **vide**.
