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
- `requirements.txt` : dépendances Python.

L'exécution du programme génère `quantum_workspace_resultats_02.json` ainsi que deux figures PNG dans le même dossier.

## Prochaine hypothèse — H2

**Réorganisation prédictive à coût contrôlé** : estimer les corrélations et les besoins futurs en ressources à partir d'une représentation compacte, puis réorganiser les calculs uniquement lorsque le bénéfice attendu dépasse le coût de cette opération.

Pour tester cette hypothèse, nous devrons comparer la précision, les performances et la mémoire à des méthodes de référence sur plusieurs systèmes et graines aléatoires.

## Ambition à long terme

Développer un laboratoire numérique de chimie quantique qui pourrait un jour aider à étudier des réactions moléculaires difficiles, notamment celles utiles en biologie et en médecine. **Aucune application médicale n'est démontrée à ce stade.**

## Références et notes

Consultez [le carnet de recherche](quantum_workspace_carnet_01.md) pour les formules, les limites expérimentales et les liens vers la littérature.