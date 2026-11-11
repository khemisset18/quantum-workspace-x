# Théorie 03 — Arbres de tenseurs : Fibonacci et intrication

**11 novembre 2026 — Expérience exploratoire vérifiée sur 8 qubits. Aucune découverte scientifique nouvelle démontrée.**

## Question

La géométrie d'un arbre de tenseurs peut-elle diminuer la taille d'une représentation mathématique exacte d'un état quantique ? Une division inspirée du nombre d'or fonctionne-t-elle mieux qu'un arbre équilibré ? Et qu'apporte une structure guidée par l'intrication ?

Nous utilisons des arbres binaires enracinés (TTN), dont les feuilles correspondent à des qubits. La variante *Fibonacci* sépare récursivement un ensemble de taille `n` en `round(n/phi)` et le reste, avec `phi=(1+sqrt(5))/2`. C'est **une heuristique géométrique**, non une propriété quantique spéciale.

## Méthode et métrique

Pour chaque arête, nous calculons le rang de Schmidt de la bipartition de l'état quantique **complet**, avec un seuil numérique de `1e-10` relatif à la plus grande valeur singulière. Le nombre rapporté est la somme des tailles des tenseurs d'un réseau exact avec ces dimensions de liaison. C'est un **nombre formel de coefficients complexes**, qui inclut des libertés de jauge : ce n'est ni de la RAM mesurée, ni une accélération observée.

Arbres comparés :

1. arbre équilibré, feuilles dans l'ordre naturel ;
2. arbre Fibonacci, feuilles dans l'ordre naturel ;
3. deux formes précédentes avec un ordre de feuilles extrait d'une hiérarchie d'information mutuelle ;
4. arbre de fusions gloutonnes guidées par l'information mutuelle moyenne ;
5. contrôle constitué de 24 permutations aléatoires par état (arbres équilibrés).

Les états : quatre paires de Bell, GHZ, état fondamental d'Ising 1D avec ordre brouillé et état aléatoire complexe. Chaque état comporte **8 qubits**.

## Résultats statiques

| État | Équilibré naturel | Fibonacci naturel | Équilibré corrélé | Fibonacci corrélé | Fusion intrication |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4 paires de Bell | 864 | 528 | **51** | 108 | **51** |
| GHZ | 84 | 84 | 84 | 84 | 84 |
| Ising 1D brouillé | 864 | **528** | 864 | **528** | **528** |
| Aléatoire | 864 | 528 | 864 | 528 | **480** |

Le fait qu'un arbre utilise moins de coefficients que l'autre **ne prouve pas** qu'il consomme moins de RAM ou qu'il s'exécute plus vite. Sur l'état aléatoire, par exemple, **528 coefficients restent supérieurs aux 256 amplitudes de l'état complet**. La méthode n'a donc pas démontré une compression utile sur ce cas.

## Exploration dynamique (illustration, pas évolution de Schrödinger)

Nous construisons 13 états en interpolant entre deux produits différents de quatre paires Bell. Trois stratégies plus un contrôle sont évaluées :

- `arbre_equilibre` : topologie équilibrée, fixée dans l'ordre naturel ;
- `arbre_fixe` : topologie choisie avec les corrélations de l'état initial ;
- `arbre_retarde` : topologie choisie avec les corrélations de l'étape **précédente** ;
- `arbre_oracle` : topologie choisie avec les corrélations exactes de l'étape **courante**.

Moyenne des coefficients formels sur les 13 étapes :

| Approche | Moyenne |
| --- | ---: |
| Équilibré naturel | 801,46 |
| Corrélation figée | 163,92 |
| Corrélation retardée | 147,54 |
| Corrélation courante (oracle) | 146,62 |

**Attention** : la stratégie retardée n'est pas un moteur prédictif, et les coûts du calcul de l'information mutuelle ou de reconstruction de l'arbre ne sont pas inclus dans les chiffres. Les états intermédiaires sont synthétiques.

## Hypothèse suivante à tester

Passer à un **MPS/TTN réellement maintenu sous forme compressée**, plutôt qu'à un état complet, afin d'estimer les corrélations localement. Comparer coût total, erreur contrôlée, mémoire de pointe et temps d'exécution, y compris reconstruction lors d'un changement de topologie. Tester ensuite un estimateur prédictif léger utilisant les statistiques des étapes précédentes.

## Exécution

```bash
python -m pip install -r requirements.txt
python quantum_workspace_tests_03.py
python quantum_workspace_theorie_03_arbres.py
```

Résultats JSON générés : `quantum_workspace_resultats_03.json`.

## Portée scientifique

Cette recherche n'établit **ni** propriété particulière du nombre d'or en physique quantique, **ni** nouveau type de calcul quantique, **ni** avancée médicale. Elle constitue une base de tests reproductibles pour comparer des géométries de réseaux de tenseurs. 
