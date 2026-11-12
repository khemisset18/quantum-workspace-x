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

## Théorie 06 — Observer sélectivement les corrélations

Le moteur observe au plus quelques paires de qubits, uniquement après des interactions déjà exécutées. Il ne voit pas le futur et maintient la représentation MPS compressée.

**Résultat :** l'observation sélective est nettement moins chère que la matrice d'information mutuelle complète, mais **pas plus efficace que la méthode simple utilisant seulement l'historique** sur nos circuits de test.

| 8 qubits, temps moyen en ms | Historique seul | Observation sélective | Corrélations complètes |
| --- | ---: | ---: | ---: |
| Motifs répétitifs | **23,3** | 49,1 | 420,2 |
| Motifs changeants | **25,4** | 55,7 | 497,6 |
| Motifs aléatoires | 74,5 | 73,7 | 719,3 |

Mesures sur un prototype Python, 6 graines, pas sur GPU. Les scénarios répétitifs et changeants sont déterministes et identiques entre graines. Les temps ne sont pas des benchmarks matériels établis.

- [Code théorie 06](quantum_workspace_theorie_06_observation_selective.py) — [Tests](quantum_workspace_tests_06.py) — [Carnet scientifique](quantum_workspace_carnet_06.md)
- Pour tester : `python quantum_workspace_tests_06.py`

**Prochaine hypothèse :** utiliser à très faible coût les informations de troncature déjà calculées par SVD pour savoir *quand* évaluer des corrélations supplémentaires, seulement si cela peut améliorer une décision. Voir [le projet de test suivant](../../issues).

## Théorie 07 — Diagnostics peu coûteux et comparaison avec la recherche existante

Cette expérience teste une **politique d'observation à budget limité**. Elle observe quelques corrélations *seulement* après un changement de régime et un signal numérique de pression MPS (dimension de liaison / poids SVD écarté). Le contrôleur **ne lit pas les opérations futures**.

**Résultat négatif utile :** sur les petits circuits synthétiques testés, la stratégie budgetée **ne bat pas** la meilleure règle simple fondée sur l'historique. C'est documenté honnêtement, avec une vérification de fidélité exacte sur 8 et 10 qubits.

| 8 qubits, temps médian par graine | Ordre fixe | Historique seul | Budgeté |
| --- | ---: | ---: | ---: |
| Répétitif | 30,8 ms | **14,6 ms** | 17,2 ms |
| Changeant | 28,8 ms | **23,5 ms** | 38,4 ms |
| Aléatoire | **38,2 ms** | 48,2 ms | 53,1 ms |

Les temps sont exploratoires (Python, un passage par graine), pas des benchmarks robustes. Les coefficients MPS ne sont pas une mesure de RAM réelle.

- [Code théorie 07](quantum_workspace_theorie_07_budget.py) · [Tests](quantum_workspace_tests_07.py) · [Carnet 07](quantum_workspace_carnet_07.md)
- [Validation externe via quimb](quantum_workspace_validation_quimb.py) (dépendance facultative dans [requirements-reference.txt](requirements-reference.txt)).
- Bibliothèques à réutiliser plutôt qu'à réécrire : [quimb](https://quimb.readthedocs.io/en/latest/circuit/circuit-mps.html), [TeNPy](https://tenpy.readthedocs.io/en/latest/reference/tenpy.networks.mps.MPS.html), [ITensorMPS](https://docs.itensor.org/ITensorMPS/stable/MPSandMPO.html), [Qiskit Aer](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html).

**Prochaine recherche :** utiliser des valeurs de Schmidt obtenues en jauge canonique, un véritable coût de RAM et plusieurs circuits hors mise au point, puis comparer à ces simulateurs établis. Aucune découverte originale ni avancée médicale n'a encore été démontrée.

## Théorie 09 — Moteur hybride à budget mémoire (MPO / SWAP)

**Retour à l'objectif principal :** simuler efficacement les systèmes quantiques sous forme MPS. Les interactions éloignées peuvent être appliquées par SWAP ou par MPO direct. Les deux sont des algorithmes déjà connus ; notre expérience compare leur coût et une règle simple qui contrôle le pic mémoire.

Sur 10 qubits et `chi=32`, notre scénario de référence `switching` conserve une fidélité finale proche de 1 :

| Approche | SWAP | Coefficients MPS au pic | Temps médian exploratoire |
| --- | ---: | ---: | ---: |
| SWAP | 160 | 2 728 | 49,72 ms |
| MPO direct | 0 | 10 896 | 41,45 ms |
| Hybride avec budget | 160 | 2 728 | 45,10 ms |

**Conclusion honnête :** MPO évite les SWAP mais peut multiplier par quatre les coefficients temporaires. La politique à budget mémoire empêche ce pic dans le scénario considéré, sans démontrer une accélération générale. Ces mesures CPU sont des prototypes, pas des benchmarks stabilisés.

- [Programme Théorie 09](quantum_workspace_theorie_09_hybride_mpo.py)
- [Tests Théorie 09](quantum_workspace_tests_09.py)
- [Carnet scientifique complet](quantum_workspace_carnet_09.md)

```bash
python quantum_workspace_tests_09.py
python quantum_workspace_theorie_09_hybride_mpo.py --n 10 --chi 32 --repeats 2 --scenario switching
```

**Prochaine piste :** compression MPO en continu pour éviter de construire tous les tenseurs temporaires, puis une règle de décision à coût et incertitude mesurés.

## Nouvelles approches — Architecture adaptative à coût total

Nous poursuivons le projet initial : **simulations quantiques MPS/TTN sur calcul classique**, avec choix adaptatif entre SWAP, MPO et méthodes de contraction, sous contraintes de mémoire, temps et précision. Les travaux sur la « friction atomique » sont hors périmètre de cette piste.

- [Revue scientifique et hypothèses testables](RECHERCHE_NOUVELLES_APPROCHES.md)
- [Théorie 10 : MPO streaming/zip-up](../../issues/5)
- [Théorie 11 : sélecteur de méthode à coût contrôlé](../../issues/6)

Aucun gain nouveau n'est encore établi : les comparaisons à fidélité égale, sur circuits non utilisés pour le réglage, constituent le critère de validation.

## Théories 10 et 11 — MPO streaming et choix adaptatif

Prototype testé et documenté : application **MPO zip-up en continu**, variante **QR** qui évite des SVD inutiles, et **sélecteur prudent** de méthode selon un budget mémoire estimé.

Les tests sur 8/10 qubits ont passé les validations de fidélité. Les performances sont **mitigées** : zip-up QR est plus rapide que notre premier zip-up SVD, mais ne bat pas systématiquement MPO direct ou SWAP ; le sélecteur n'a pas encore démontré d'avantage contre la meilleure méthode simple. Les petites différences RSS sont dans le bruit des mesures.

- [Code du simulateur MPO streaming et sélecteur](quantum_workspace_theorie_10_11_zipup_selector.py)
- [Tests automatiques](quantum_workspace_tests_10_11.py)
- [Carnet avec chiffres, limites et protocole](quantum_workspace_carnet_10_11.md)
- [Benchmarks GitHub Actions isolés](https://github.com/khemisset18/quantum-workspace-x/actions/runs/43124140646)

```bash
python quantum_workspace_tests_10_11.py
python quantum_workspace_theorie_10_11_zipup_selector.py --n 10 --chi 32 --repeats 2 --scenario random --seed 11
```

La prochaine amélioration testera un contrôle de coût calibré et des méthodes zip-up de référence disponibles dans **quimb**, sur des circuits plus longs et des problèmes physiques, à précision comparable.

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
- `quantum_workspace_theorie_06_observation_selective.py`, `quantum_workspace_tests_06.py` et `quantum_workspace_carnet_06.md` : observation sélective et résultats.
- `requirements.txt` : dépendances Python.

L'exécution du programme génère `quantum_workspace_resultats_02.json` ainsi que deux figures PNG dans le même dossier.

## Hypothèse à poursuivre — contrôle adaptatif

**Réorganisation prédictive à coût contrôlé** : estimer les corrélations et les besoins futurs en ressources à partir d'une représentation compacte, puis réorganiser les calculs uniquement lorsque le bénéfice attendu dépasse le coût de cette opération.

Pour tester cette hypothèse, nous devrons comparer la précision, les performances et la mémoire à des méthodes de référence sur plusieurs systèmes et graines aléatoires.

## Ambition à long terme

Développer un laboratoire numérique de chimie quantique qui pourrait un jour aider à étudier des réactions moléculaires difficiles, notamment celles utiles en biologie et en médecine. **Aucune application médicale n'est démontrée à ce stade.**

## Références et notes

Consultez [le carnet de recherche](quantum_workspace_carnet_01.md) pour les formules, les limites expérimentales et les liens vers la littérature.