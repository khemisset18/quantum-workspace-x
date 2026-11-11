# Théorie 05 — Prévoir les corrélations à partir d'un MPS, sans regarder les portes futures

**11 novembre 2026 — Étude pilote reproductible. Aucune nouvelle loi physique ni découverte démontrée.**

## Hypothèse

Le réarrangement d'un **matrix product state** (MPS) pourrait réduire le routage de certaines interactions lorsque la structure des corrélations varie lentement. Une extrapolation de la matrice d'information mutuelle quantique pourrait être utile, **mais seulement si le coût d'observer et de réorganiser est inférieur à l'économie obtenue**.

Une limite fondamentale apparaît immédiatement : deux systèmes ayant exactement le même état à un instant donné peuvent avoir des évolutions d'intrication différentes si leurs interactions ultérieures diffèrent. Sans hypothèse sur la dynamique, il n'existe donc pas de prédiction universelle du futur à partir de l'état seul. Le test `check_impossibility_of_universal_prediction` le démontre sur un état produit : porte identité versus porte `ZZ(pi/4)`.

## Ce qui est réellement implémenté

Le programme `quantum_workspace_theorie_05_history_mps.py` maintient les états **directement sous forme MPS** et calcule les matrices densité de 1 et 2 sites par contraction d'environnements MPS, sans reconstruire le vecteur d'état complet.

Il calcule l'information mutuelle `I(i:j)=S(rho_i)+S(rho_j)-S(rho_ij)`, puis extrapole :

```text
I_prédit(t+1) = clip(I(t) + 0,7 * [I(t) - I(t-1)], 0, 2)
```

**Attention : l'information mutuelle contient des corrélations classiques et quantiques ; elle n'est pas une mesure pure d'intrication.** Aucun réseau neuronal n'est encore entraîné.

Six politiques sont comparées :

- `fixed` : ordre immobile ;
- `history` : utilise uniquement les paires des portes **déjà exécutées** ;
- `history_confident` : même historique, mais réorganisation uniquement si les **deux dernières étapes** montrent le même ensemble de paires ;
- `reactive` : utilise l'information mutuelle du dernier état compressé ;
- `trend` : extrapole cette information mutuelle sur les deux dernières observations ;
- `oracle` : **utilise les portes de l'étape suivante** (borne favorable, pas un prédicteur admissible).

Aucune politique sauf `oracle` n'a accès aux portes futures pendant sa décision. La simulation dense indépendante est uniquement utilisée **après** le calcul pour vérifier la fidélité quand n<=10.

## Trois scénarios de circuits

- `persistent` : mêmes appariements pendant huit étapes, puis modification ;
- `switching` : changements de groupes d'appariements toutes les quatre étapes ;
- `random` : nouvel appariement aléatoire à chaque étape (contrôle négatif).

Toutes les expériences ont 12 étapes et des rotations locales. Les chiffres ne mesurent pas une accélération quantique.

## Résultats : 8 qubits, chi=16, 6 graines (11, 12, 13, 14, 15, 31)

### Moyenne du nombre de SWAP (y compris réorganisations)

| Politique | Persistant | Changements périodiques | Aléatoire |
|---|---:|---:|---:|
| Fixe | 288,0 | 192,0 | 210,7 |
| Historique | **66,0** | **76,0** | 258,0 |
| Historique + confiance | 114,0 | 132,0 | **211,0** |
| Information mutuelle réactive | 66,0 | 162,0 | 211,2 |
| Information mutuelle extrapolée | 66,0 | 162,0 | 223,0 |
| Oracle (connaît le futur) | 18,0 | 20,0 | 70,0 |

La stratégie fondée uniquement sur les portes antérieures est **très compétitive sur les scénarios réguliers**. Sur le scénario aléatoire, elle peut être contre-productive. La règle de confiance évite presque toutes ces réorganisations inutiles.

### Temps médians sur une exécution locale (secondes)

| Politique | Persistant | Changements périodiques | Aléatoire |
|---|---:|---:|---:|
| Fixe | 0,072 | 0,053 | 0,055 |
| Historique | 0,021 | 0,026 | 0,062 |
| Historique + confiance | 0,033 | 0,036 | 0,056 |
| Information mutuelle réactive | 0,435 | 0,451 | 0,525 |
| Extrapolation d'information mutuelle | 0,431 | 0,444 | 0,525 |

Ces durées sont indicatives : **un seul processus local par essai, pas de repetitions statistiques par graine ni de comparaison machine indépendante**. En particulier, les mesures d'information mutuelle coûtent plus cher que les SWAP économisés à cette petite échelle.

Sur ces circuits, l'extrapolation des corrélations peut diminuer l'erreur de prévision brute par rapport au maintien d'une carte constante, mais elle **n'améliore pas systématiquement le routage** par rapport à la méthode réactive. De meilleurs scores prédictifs ne suffisent pas à justifier une architecture plus complexe.

La fidélité finale mesurée par rapport au calcul dense, sur ces expériences 8 qubits, est numériquement proche de **1 pour toutes les politiques**.

## Vérification supplémentaire : 10 qubits, chi=32, graine 15

| Scénario | Fixe (SWAP) | Historique | Historique + confiance | Extrapolation MI |
|---|---:|---:|---:|---:|
| Persistant | 480 | **110** | 190 | 110 |
| Changements | 320 | **125** | 217 | 223 |
| Aléatoire | 364 | 463 | **364** | 333 |

La fidélité reste proche de 1 dans cette configuration, mais le **nombre maximal de coefficients MPS reste identique** entre les différentes politiques non oracle : **2 728**. Ne pas annoncer une réduction de RAM sur ces expériences.

## Protocole de reproduction

```bash
python -m pip install -r requirements.txt
python quantum_workspace_tests_05.py
python quantum_workspace_theorie_05_history_mps.py --n 8 --chi 16 --seed 15
python quantum_workspace_theorie_05_history_mps.py --n 10 --chi 32 --seed 15
```

Chaque exécution génère `quantum_workspace_resultats_05_n{n}_seed{seed}.json`. Pour une mesure temporelle sérieuse, fixer le nombre de fils BLAS et répéter les chronométrages sur une machine dédiée.

## Leçons importantes

1. **Ne pas prédire ce qui peut être observé ou estimé moins cher** : un historique des portes peut surpasser la carte d'information mutuelle complète.
2. **Savoir s'abstenir** : la stabilité de l'historique fournit un premier signal de confiance.
3. **Facturer le coût complet** : la complexité des estimations peut annuler les économies de routage.
4. **Mesurer le bon objectif** : SWAP, mémoire des tenseurs, RAM réelle, durée, fidélité et erreurs d'observables ne sont pas interchangeables.
5. **Ne pas présumer une nouveauté** : cette étude assemble des méthodes et contrôles simples ; aucune supériorité sur les meilleures bibliothèques existantes n'est établie.

## Étape 06 proposée

Construire un **contrôleur sélectif** : historique de portes à bas coût par défaut ; observation locale d'un petit nombre de liaisons MPS uniquement lorsque la confiance baisse ; choix d'un réarrangement si l'économie probable dépasse le coût réel du diagnostic et des permutations. Comparer à un routage statique optimisé, à des bibliothèques spécialisées et à plusieurs familles de systèmes physiques, avec erreur égale, RAM de pointe et temps médian sur répétitions.

### Lectures scientifiques pertinentes

- [On the Ordering of Sites in DMRG using Quantum Mutual Information](https://arxiv.org/abs/2103.01111) : structure des corrélations et ordre des sites.
- [On the fly swapping algorithm for ordering of degrees of freedom in DMRG](https://pubmed.ncbi.nlm.nih.gov/35378514/) : réorganisation pendant le calcul, méthode déjà connue.
- [Direct entanglement detection of quantum systems using machine learning](https://www.nature.com/articles/s41534-025-00970-w) : prédiction de métriques d'intrication à partir de données antérieures, étude de 2025.
- [Time-Dependent Variational Principle with Controlled Bond Expansion for MPS](https://doi.org/10.1103/PhysRevLett.133.026401) : adaptation de la dimension de liaison.
