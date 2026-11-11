# Quantum Workspace X 🔬

**Recherche expérimentale sur la simulation quantique, les réseaux de tenseurs et le calcul adaptatif.**

Ce projet explore une question : **peut-on mieux représenter les corrélations quantiques pour rendre certains calculs plus accessibles sur des ordinateurs classiques ?**

## Premier prototype — Carte de l'intrication (Théorie 01)

Le prototype simule quatre états de **8 qubits** : quatre paires de Bell, GHZ, un état fondamental du modèle d'Ising 1D (avec ordre de qubits brouillé) et un état aléatoire.

Il :
1. calcule l'information mutuelle quantique entre les paires de qubits ;
2. cherche un ordre minimisant la somme des informations mutuelles pondérées par les distances ;
3. compare les dimensions de liaison nécessaires pour représenter les états en **MPS** avec une fidélité d'au moins **99,99 %** ;
4. génère des données JSON et deux graphiques, si Matplotlib est installé.

### Résultats de référence

| État | Dimension MPS initiale | Après réorganisation |
| --- | ---: | ---: |
| 4 paires de Bell | 16 | 2 |
| GHZ | 2 | 2 |
| Ising 1D (ordre brouillé) | 7 | 4 |
| État aléatoire | 16 | 15 |

Il s'agit de dimensions de liaison, **pas** de mesures du temps d'exécution ou de la consommation réelle de RAM/GPU. La recherche exhaustive des permutations ne passe pas à l'échelle.

**Important : ces techniques d'optimisation sont déjà connues et les résultats ne constituent pas une découverte scientifique nouvelle.** L'objectif est de construire un banc d'essai contrôlé avant d'évaluer des hypothèses originales.

## Nouvelles expériences — Géométrie et arbres de tenseurs

**Théorie 02 — Nombre d'or.** Test d'un ordre quasi-périodique fondé sur `phi`, comparé à un ordre naturel, aléatoire et guidé par les corrélations. **Pas d'avantage universel du nombre d'or démontré.**

- Programme : [Théorie 02](quantum_workspace_theorie_02_nombre_or.py)
- Protocole et résultats : [Carnet 02](quantum_workspace_carnet_02.md)

**Théorie 03 — Arbres Fibonacci et intrication.** Comparaison de cinq architectures arborescentes exactes, plus des contrôles aléatoires, sur 8 qubits. Un test dynamique confronte une topologie fixe, une topologie décalée d'un pas et un oracle utilisant les corrélations de l'état courant.

| Cas : 4 paires intriquées | Coefficients TTN formels |
| --- | ---: |
| Arbre équilibré, ordre naturel | 864 |
| Arbre Fibonacci, ordre naturel | 528 |
| Arbre guidé par l'intrication | **51** |

Ce sont des **comptes de coefficients mathématiques**, et non des mesures de RAM ou de temps. Les calculs conservent l'état complet, et le résultat ne démontre pas encore une accélération.

- Programme : [Théorie 03](quantum_workspace_theorie_03_arbres.py)
- Tests : [Tests 03](quantum_workspace_tests_03.py)
- Protocole, limites et résultats : [Carnet 03](quantum_workspace_carnet_03.md)

```bash
python quantum_workspace_tests_01.py
python quantum_workspace_tests_02.py
python quantum_workspace_tests_03.py
python quantum_workspace_theorie_03_arbres.py
```

## Théorie 04 — Routage anticipatif avec un MPS directement compressé

Notre simulateur maintient maintenant l'état quantique sous forme de tenseurs **MPS** pendant l'évolution. Sur des circuits structurés de 8 et 10 qubits, il compare cinq organisations, dont une stratégie anticipant les **interactions futures connues**, une stratégie réactive, un ordre inspiré du nombre d'or et un contrôle statique compilé.

| Indicateur | Ordre naturel | Anticipatif |
| --- | ---: | ---: |
| SWAP, 8 qubits (`chi=16`) | 192 | **20** |
| Coefficients maximum, 8 qubits | 680 | 680 |
| SWAP, 10 qubits (`chi=16`) | 320 | **33** |
| Coefficients maximum, 10 qubits | 1 704 | **1 192** |
| Fidélité finale, 10 qubits | 0,1423 | ~1,0000 |

Ces résultats sont propres aux circuits expérimentés. Ils ne constituent **ni une découverte d'algorithme quantique ni une prédiction de l'intrication** : l'algorithme consulte les opérations déjà prévues. Les stratégies ne sont pas toutes à fidélité égale à `chi=16`. À 10 qubits et **chi=32**, toutes retrouvent une fidélité proche de 1 ; les coefficients MPS maximum sont de **2 728 (ordre naturel) contre 1 192 (anticipatif)**. Cela correspond à une réduction de taille mathématique des tenseurs d'environ 56 %, **pas** à une économie de RAM mesurée.

- [Code de la théorie 04](quantum_workspace_theorie_04_predictive_mps.py)
- [Tests numériques de la théorie 04](quantum_workspace_tests_04.py)
- [Carnet scientifique, protocole et limites](quantum_workspace_carnet_04.md)

```bash
python quantum_workspace_tests_04.py
python quantum_workspace_theorie_04_predictive_mps.py --n 8 --chi 16
python quantum_workspace_theorie_04_predictive_mps.py --n 10 --chi 16
```

## Théorie 05 — Faire mieux qu'une prédiction complexe

Dans cette étape, nous testons un **contrôleur de réorganisation MPS qui n'utilise pas les interactions futures**. Il compare l'ordre fixe, une heuristique à partir des portes passées, une règle de confiance, l'information mutuelle quantique et son extrapolation. Un oracle qui connaît l'étape suivante sert seulement de limite théorique.

Six graines de test, 8 qubits, 12 étapes :

| Politique | SWAP moyens (interactions répétées) | SWAP moyens (interactions aléatoires) |
|---|---:|---:|
| Ordre fixe | 288,0 | 210,7 |
| Historique des portes | **66,0** | 258,0 |
| Historique + règle de confiance | 114,0 | **211,0** |
| Corrélations MPS extrapolées | 66,0 | 223,0 |

**Résultat honnête :** notre prédicteur basé sur la matrice complète d'information mutuelle ne gagne pas en temps total sur ces exemples, malgré certaines économies de SWAP. Une stratégie beaucoup moins coûteuse, basée sur l'historique, est préférable sur les circuits réguliers. Une règle de confiance empêche presque toutes les réorganisations inutiles quand les interactions sont aléatoires.

Les fidélités sur 8 qubits sont proches de 1. Ces résultats ne démontrent **ni** une découverte scientifique **ni** une réduction de mémoire réelle.

- [Prototype de la théorie 05](quantum_workspace_theorie_05_history_mps.py)
- [Tests et contre-exemple de prédiction universelle](quantum_workspace_tests_05.py)
- [Carnet 05 — hypothèse, protocole, limites et résultats](quantum_workspace_carnet_05.md)

```bash
python quantum_workspace_tests_05.py
python quantum_workspace_theorie_05_history_mps.py --n 8 --chi 16 --seed 15
```

## Installation

Python 3.10+ recommandé :

```bash
python -m pip install -r requirements.txt
python quantum_workspace_tests_01.py
python quantum_workspace_theorie_01.py
```

Pour la démonstration la plus simple (NumPy uniquement) :

```bash
python quantum_workspace_experience_01.py
```

## Organisation

- `quantum_workspace_experience_01.py` : démonstration initiale des rangs de Schmidt.
- `quantum_workspace_theorie_01.py` : algorithme expérimental et graphiques.
- `quantum_workspace_tests_01.py` : tests de cohérence.
- `quantum_workspace_carnet_01.md` : méthode, limites, résultats et références scientifiques.
- `quantum_workspace_theorie_02_nombre_or.py` et `quantum_workspace_tests_02.py` : hypothèse d'ordre doré.
- `quantum_workspace_theorie_03_arbres.py` et `quantum_workspace_tests_03.py` : arbres de tenseurs et tests.
- `quantum_workspace_carnet_02.md` et `quantum_workspace_carnet_03.md` : protocoles expérimentaux et limites.
- `quantum_workspace_theorie_05_history_mps.py` et `quantum_workspace_tests_05.py` : prédiction historique, contrôles négatifs et vérification.
- `quantum_workspace_carnet_05.md` : carnet scientifique de la théorie 05.
- `requirements.txt` : dépendances Python.

L'exécution du programme génère `quantum_workspace_resultats_02.json` ainsi que deux figures PNG dans le même dossier.

## Hypothèse à poursuivre — contrôle adaptatif

**Réorganisation prédictive à coût contrôlé** : estimer les corrélations et les besoins futurs en ressources à partir d'une représentation compacte, puis réorganiser les calculs uniquement lorsque le bénéfice attendu dépasse le coût de cette opération.

Pour tester cette hypothèse, nous devrons comparer la précision, les performances et la mémoire à des méthodes de référence sur plusieurs systèmes et graines aléatoires.

## Ambition à long terme

Développer un laboratoire numérique de chimie quantique qui pourrait un jour aider à étudier des réactions moléculaires difficiles, notamment celles utiles en biologie et en médecine. **Aucune application médicale n'est démontrée à ce stade.**

## Références et notes

Consultez [le carnet de recherche](quantum_workspace_carnet_01.md) pour les formules, les limites expérimentales et les liens vers la littérature.