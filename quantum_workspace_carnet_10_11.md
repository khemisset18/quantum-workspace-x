# Quantum Workspace X — Carnet scientifique 10/11 : MPO streaming et sélection de méthode

**12 novembre 2026.** Statut : **implémentation fonctionnelle et vérifiée sur de petits circuits, mais aucun avantage de performance général établi**.

## Notre question
Peut-on diminuer le coût de la simulation MPS en choisissant automatiquement entre le routage **SWAP**, l'application directe d'un **MPO**, et l'application de MPO **zip-up** à la volée ?

Le projet est toujours centré sur la simulation quantique **classique**. Aucun rapport avec la friction atomique n'est étudié ici.

### Méthodes de référence déjà connues
- **SWAP** : rapprocher les sites, appliquer la porte, remettre les qubits logiques dans leur position initiale.
- **MPO direct** : application d'un MPO de liaison 2 pour `exp(-i theta Z_i Z_j)`, puis canonisation et compression ; voir Théorie 09.
- **Zip-up** : application site par site d'un MPO à une MPS avec factorisation intermédiaire, sans créer d'abord tous les tenseurs MPO×MPS agrandis ; connue depuis les travaux METTS (Stoudenmire & White, 2010). [Description de l'algorithme](https://tensornetwork.org/mps/algorithms/zip_up_mpo/).
- **Zip-up + QR** : variante expérimentale accélérant certaines étapes qui ne tronquent pas, puis effectuant la même compression SVD finale.
- **Sélecteur à budget** : choisit SWAP ou zip-up+QR selon la distance et une borne conservatrice de taille de tenseurs ; aucune lecture de portes futures.

**Attention** : le zip-up à troncation locale n'offre pas, en général, une garantie directe d'erreur globale. Nous comparons donc les états finaux à une référence indépendante pour n ≤ 10. La bibliothèque [quimb propose déjà des méthodes MPO zip-up](https://quimb.readthedocs.io/en/latest/autoapi/quimb/tensor/tn1d/compress/index.html) ; notre implémentation est expérimentale, **pas une invention de zip-up**.

## Implémentation

Programme : [`quantum_workspace_theorie_10_11_zipup_selector.py`](quantum_workspace_theorie_10_11_zipup_selector.py).

Le zip-up ne matérialise pas tout le MPS temporaire agrandi comme dans MPO eager. Il crée et contracte successivement un tenseur de MPO, puis factorise la matrice intermédiaire ; une passe de canonisation et une compression finale contrôlent la dimension de liaison. La variante QR remplace certaines SVD quand il n'y a pas de réduction de rang à effectuer lors de la première passe. Le contrôleur n'examine que la porte actuelle et la structure MPS courante.

Les comparaisons n'emploient **pas** de GPU. Elles ne servent pas encore de test de capacité à grande échelle.

## Contrôles et résultats

- GitHub Actions, Python 3.11, `OPENBLAS_NUM_THREADS=1`.
- Chaque mode a été lancé dans **un processus distinct**, afin que la mémoire maximale (`ru_maxrss`) soit mesurée indépendamment.
- 8 qubits (`chi=16`) ou 10 qubits (`chi=32`), deux répétitions de circuit et une graine (`seed=11`) par scénario.
- Les fidélités calculées contre le vecteur exact sont proches de 1 dans chaque cas.
- Temps rapportés ci-dessous : **une seule exécution par politique/scénario**. Aucune comparaison statistique solide n'est possible.

### 8 qubits, interactions aléatoires

| Méthode | Temps (ms) | RSS maximum (KiB) | SWAP | SVD |
| --- | ---: | ---: | ---: | ---: |
| SWAP | 12,9 | 48 912 | 112 | 136 |
| MPO direct | **12,8** | 49 036 | 0 | 80 |
| Zip-up SVD | 18,1 | 49 028 | 0 | 158 |
| Zip-up QR | 15,6 | 49 024 | 0 | 80 |
| Sélecteur à budget | 14,3 | 48 928 | 78 | 119 |

### 10 qubits, interactions aléatoires

| Méthode | Temps (ms) | RSS maximum (KiB) | SWAP | SVD |
| --- | ---: | ---: | ---: | ---: |
| SWAP | **31,0** | 50 144 | 168 | 198 |
| MPO direct | 32,1 | 50 328 | 0 | 114 |
| Zip-up SVD | 45,7 | 50 276 | 0 | 221 |
| Zip-up QR | 37,1 | 50 128 | 0 | 114 |
| Sélecteur à budget | 33,0 | 50 024 | 140 | 184 |

### 10 qubits, interactions changeantes

| Méthode | Temps (ms) | RSS maximum (KiB) | SWAP | SVD |
| --- | ---: | ---: | ---: | ---: |
| SWAP | 32,2 | 50 012 | 160 | 190 |
| MPO direct | **27,7** | 50 424 | 0 | 110 |
| Zip-up SVD | 39,6 | 50 368 | 0 | 208 |
| Zip-up QR | 33,3 | 50 272 | 0 | 110 |
| Sélecteur à budget | 31,0 | 50 180 | 112 | 166 |

**Interprétation :** le QR réduit le nombre de décompositions SVD de la première passe et améliore le temps du zip-up SVD dans ces exécutions. Malgré cela, le zip-up QR reste **plus lent que la meilleure référence** pour les trois cas testés. Le sélecteur n'a pas démontré de bénéfice décisif.

Le RSS global inclut Python, NumPy et leurs bibliothèques ; les différences de quelques centaines de KiB sont **trop petites pour établir un gain mémoire**. Le nombre d'opérations SWAP ne suffit pas non plus à mesurer la vitesse.

## Reproduction

```bash
python -m pip install -r requirements.txt
python quantum_workspace_tests_10_11.py
python quantum_workspace_theorie_10_11_zipup_selector.py --n 8 --chi 16 --repeats 2 --scenario random --seed 11
python quantum_workspace_theorie_10_11_zipup_selector.py --n 10 --chi 32 --repeats 2 --scenario random --seed 11
python quantum_workspace_theorie_10_11_zipup_selector.py --n 10 --chi 32 --repeats 2 --scenario switching --seed 11
```

Résultats individuels isolés disponibles sous forme d'artefacts du workflow GitHub Actions :
[Benchmarks MPO / zip-up (exécution du 12 novembre 2026)](https://github.com/khemisset18/quantum-workspace-x/actions/runs/43124140646).

## Prochaine expérience, plus pertinente

1. **Éviter les doubles factorisations :** évaluer des variantes de zip-up déjà optimisées dans quimb, et un sweep directionnel, avant toute nouvelle réécriture.
2. **Choisir le meilleur algorithme sur la vraie plateforme** : calibrer (sur circuits d'entraînement uniquement) le coût temporel et la RAM selon la distance des qubits, les dimensions de liaison et l'erreur.
3. **Vérifier des gains avec des circuits plus grands** (12–24 qubits), davantage de graines indépendantes, différentes structures de corrélation et plusieurs valeurs de `chi`.
4. **Contrôler la précision hors du régime dense** : normes, observables locales, convergence par rapport à `chi` et comparaison indépendante à quimb ou ITensor.
5. **Faire une vraie comparaison statistique** : nombreuses répétitions, médianes et intervalles, mémoire de pointe au niveau du processus ou d'un instrument dédié.
6. **Exiger une amélioration robuste** contre la meilleure méthode simple à erreur comparable. Si cette amélioration n'apparaît pas, conserver l'algorithme établi plutôt qu'un sélecteur inutile.

## Conclusion
Nous avons une **expérience reproductible utile**, y compris un échec honnête : la première approche « zip-up + sélecteur » n'est pas supérieure à l'état actuel du projet sur les benchmarks testés. Les méthodes utilisées existaient avant notre recherche. La prochaine contribution potentielle serait un ordonnanceur de calcul peu coûteux validé sur de vraies simulations plus complexes, pas l'invention du zip-up lui-même.
