# Quantum Workspace X — Carnet 09 : MPO direct, SWAP et politique à budget mémoire

**Statut : prototype expérimental, méthodes numériques déjà connues, aucune nouvelle loi quantique démontrée.**

Le projet reste centré sur la simulation classique de systèmes quantiques par réseaux de tenseurs MPS. L'étude de la friction atomique n'est pas poursuivie dans cette expérience.

## Hypothèse

Au lieu de toujours rapprocher deux qubits distants par des SWAP, on peut appliquer l'interaction `exp(-i θ Z_i Z_j)` avec un opérateur MPO de liaison 2, puis compresser le MPS. Le MPO évite les opérations SWAP, mais peut augmenter la mémoire temporaire. Une politique peut-elle choisir au cas par cas entre SWAP et MPO ?

**L'utilisation d'un MPO pour des interactions éloignées est une technique connue.** Ici, nous testons un choix hybride et transparent.

## Méthodes

Les quatre modes sont :
- `swap` : routage par SWAP avant/après une porte ZZ ;
- `mpo` : MPO de dimension auxiliaire 2 appliqué directement entre les sites éloignés, suivi d'une remise en forme canonique droite par QR puis d'une compression SVD gauche-droite ;
- `hybrid` : MPO si distance MPS >= 3, sinon SWAP ;
- `hybrid_budget` : même règle, mais n'accepte le MPO que si la taille prévue de tous les tenseurs MPO, avant compression, est au plus **deux fois** la taille MPS courante.

Le contrôleur ne lit aucune porte future. Il lit seulement les indices de la porte actuelle, la topologie MPS et les tailles courantes des tenseurs.

**Point de méthode important :** pendant la mise au point, une compression locale sans canonisation a dégradé la fidélité même à dimension de liaison suffisante. La version publiée effectue une canonisation droite avant troncature et a passé les tests indépendants 6/8/10 qubits.

Les métriques incluent durée CPU exploratoire, SWAP, SVD, nombre maximal de coefficients des tenseurs MPS (y compris le MPO temporaire) et fidélité à une évolution dense indépendante pour n <= 10. Le nombre de coefficients n'est **pas** une mesure de la RAM résidente ou de la mémoire temporaire de NumPy.

## Résultats — 10 qubits, chi=32, scénario switching

Trois graines (11, 15, 23), deux répétitions du circuit par simulation. Les circuits `switching` sont identiques entre graines (les graines ne définissent pas trois problèmes physiques indépendants).

| Politique | SWAP (médiane) | Pic de coefficients (médiane) | Temps (médiane, ms) | Fidélité |
| --- | ---: | ---: | ---: | --- |
| SWAP | 160 | 2 728 | 49,72 | ~1 |
| MPO | **0** | 10 896 | 41,45 | ~1 |
| Hybride distance | 0 | 10 896 | 45,06 | ~1 |
| Hybride budget | 160 | **2 728** | 45,10 | ~1 |

Ce cas met en évidence un compromis net : MPO évite le routage mais multiplie par environ **4** le pic des coefficients MPS. Le budget mémoire évite le pic et conserve la précision, sans gain de temps fiable démontré.

## Résultats — 10 qubits, chi=32, scénario random

| Politique | SWAP (médiane) | Pic de coefficients (médiane) | Temps (médiane, ms) |
| --- | ---: | ---: | ---: |
| SWAP | 168 | 2 728 | 46,54 |
| MPO | 0 | 10 860 | 43,93 |
| Hybride distance | 10 | 10 860 | 42,33 |
| Hybride budget | 164 | **4 764** | 48,04 |

Sur le scénario aléatoire, les graines décrivent des circuits distincts. Trois répétitions ne suffisent **pas** pour trancher une faible différence de temps.

## Résultats complémentaires

- 8 qubits, chi=16, switching : SWAP 96 pour la stratégie classique et 0 pour MPO/hybride ; pic **680 vs 2 704** coefficients, fidélité ~1.
- 12 qubits, chi=32, random : l'évolution sous forme compressée fonctionne mais **aucune validation dense indépendante de fidélité** n'est effectuée au-delà de 10 qubits.
- 10 qubits, chi=16 : certaines stratégies ont une fidélité faible (par exemple environ 0,65 contre 0,77 en switching). Comparer uniquement les temps et les SWAP serait trompeur. Pour les conclusions ci-dessus, on retient chi=32 où les fidélités sont équivalentes.

## Résultat scientifique

1. Les deux méthodes appliquent exactement la même interaction théorique.
2. Direct MPO réduit les SWAP, mais peut demander davantage de mémoire temporaire.
3. Notre politique `hybrid_budget` limite le pic de coefficients dans plusieurs scénarios, au prix d'un plus grand nombre de SWAP.
4. **Aucune supériorité universelle n'est démontrée.**

## Pistes nouvelles à tester ensuite

1. **MPO « streaming / zip-up » :** construire et compresser progressivement le MPO sans matérialiser tout le MPS agrandi. Cela pourrait réduire le pic temporaire qui pénalise cette expérience.
2. **Politique de coût apprise mais prudente :** prédire le temps et le pic mémoire à partir des dimensions de liaisons, du type de porte et de la distance ; choisir la méthode avec une marge de confiance, et se rabattre sur SWAP en cas d'incertitude.
3. **Précision locale sous contrainte globale :** redistribuer le budget de troncature SVD selon les régions qui risquent de perdre le plus de précision.
4. **Benchmarks physiques :** passer progressivement de circuits synthétiques à Heisenberg, Ising 2D réduit et systèmes moléculaires de référence, en comparant à `quimb`, `TeNPy` et `MQT YAQS`.

Les options 1 et 2 ne seraient originales que si les performances dépassaient les meilleurs logiciels existants sur un jeu de tests indépendant.

## Références

- [MQT YAQS : simulation des portes via MPO, SWAP ou TDVP](https://mqt.readthedocs.io/projects/yaqs/en/latest/examples/simulation_parameters.html).
- [Exemple expérimental d'un MPO de liaison 2 pour des sites non voisins](https://pmc.ncbi.nlm.nih.gov/articles/PMC12422974/).
- [Simulation de circuits par TDVP locale (2025)](https://arxiv.org/abs/2508.10096).
- [ITensor : compression et canonisation des MPS](https://github.com/ITensor/ITensorMPS.jl/blob/main/docs/src/examples/MPSandMPO.md).

## Exécution

```bash
python -m pip install -r requirements.txt
python quantum_workspace_tests_09.py
python quantum_workspace_theorie_09_hybride_mpo.py --n 10 --chi 32 --repeats 2 --scenario switching
```

Les résultats détaillés sont sauvegardés en JSON dans le répertoire du script. Pour les expériences de plus de 10 qubits, la fidélité reste non évaluée tant qu'une validation indépendante n'est pas ajoutée.
