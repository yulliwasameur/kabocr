# KabOCR — OCR libre pour le kabyle (écriture latine)

**Essayer en ligne : https://yulliwasameur.github.io/kabocr/**. Déposez un PDF ou une image : vous obtenez le texte et un PDF cherchable. Tout se passe dans votre navigateur, et rien n'est envoyé.

*English below.*

## Ce que contient ce dépôt

| Dossier | Contenu | Licence |
|---|---|---|
| `docs/` | L'application web (une page, sans serveur) : pdf.js + tesseract.js + le modèle | Apache-2.0 (code) |
| `models/` | Le modèle **KabOCR-Free v0.1** (`kabocr-free-v0.1.traineddata`, 3,5 Mo, pour Tesseract ≥ 4.1) | **CC BY-SA 4.0** |
| `cli/kabocr.py` | Outil en ligne de commande : un PDF ou une image en entrée, un `.txt` et un PDF cherchable en sortie | Apache-2.0 |
| `tool/` | `kabocr-eval` : mesure de la qualité d'un OCR kabyle (CER, WER, **DCER** sur les lettres kabyles, sosies, règles de qualité, statistiques par document) | Apache-2.0 |
| `scripts/` | Les scripts de recherche qui reproduisent les résultats du papier | Apache-2.0 |
| `documentation/` | Fiche des jeux de test (datasheet), guide d'annotation | CC BY 4.0 |

## Utiliser le modèle

**Dans le navigateur** : https://yulliwasameur.github.io/kabocr/

**En ligne de commande** (il faut Tesseract ≥ 4.1 et poppler-utils) :

```bash
git clone https://github.com/yulliwasameur/kabocr && cd kabocr
python3 cli/kabocr.py mon-document.pdf      # -> mon-document-kabocr.txt et mon-document-kabocr.pdf
```

**Avec Tesseract directement** :

```bash
tesseract page.png sortie --tessdata-dir models -l kabocr-free-v0.1
```

## Précision (lignes imprimées réelles, jamais vues à l'entraînement)

Erreur par caractère (CER), en % ; plus c'est bas, mieux c'est.

| Système | Mémoires (Bouira) | Mémoires (Béjaïa) | Livres d'éditeurs |
|---|---|---|---|
| Tesseract `Latin` (généraliste) | 3,42 | 3,26 | 4,10 |
| Tesseract `kab` v6 (meilleur modèle public mesuré) | 1,45 | 1,36 | 2,58 |
| **KabOCR-Free v0.1 (ce dépôt)** | **0,90** | **0,75** | **1,70** |

KabOCR-Free bat le meilleur modèle public sur **chacun** des 39 documents de test. Les modèles plus précis du projet (CER de 0,39 à 0,69 %) ont appris sur des mémoires et des livres dont les droits ne permettent pas la publication : ils ne sont **pas** distribués.

## Limites

- Imprimé en écriture latine seulement : ni tifinagh, ni arabe, ni manuscrit.
- La lettre **ţ** et la notation phonétique (ə, ṯ, ḏ…) ne sont pas dans l'alphabet de ce modèle.
- Les scans flous, très petits ou en très basse résolution font monter les erreurs. **Relisez toujours le texte.**

## Citer

Voir `CITATION.cff`. Un DOI Zenodo est attribué à chaque version.

> Ameur, Y. (2026). *KabOCR: open OCR for Kabyle (Latin script)*, version 0.1.0 [Logiciel]. Zenodo.

## Licences

- Code : Apache-2.0 (`LICENSE`).
- Poids du modèle : CC BY-SA 4.0 (`LICENSE-MODEL.txt`). Le modèle a appris sur des phrases de Wikipédia en kabyle (CC BY-SA 4.0). Il dérive du modèle Tesseract `kab` de Bouaziz Ait Driss (Apache-2.0).
- Bibliothèques fournies dans `docs/vendor/` : tesseract.js et pdf.js (Apache-2.0), pdf-lib (MIT). Voir `NOTICE.md`.

---

## English

**KabOCR** is free OCR for Kabyle (Taqbaylit) in Latin script.

- **Web app** (runs fully in your browser): https://yulliwasameur.github.io/kabocr/
- **Model**: `models/kabocr-free-v0.1.traineddata` (Tesseract LSTM, CC BY-SA 4.0). It was trained only on openly licensed text (Kabyle Wikipedia rendered in 77 free fonts).
- **Accuracy**: CER of 0.90 / 0.75 / 1.70 % on unseen real theses and books, against 1.45 / 1.36 / 2.58 % for the best public model we measured.
- **Evaluation toolkit**: `tool/` (`pip install ./tool`). It reports CER, WER and DCER, the error rate on Kabyle-specific letters, split into missed and spurious.
- **Command line**: `python3 cli/kabocr.py file.pdf`.

Author: Yulliwas Ameur (Efrei Research Lab; Cnam, CEDRIC).
