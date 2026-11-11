# Théorie 02 — L'organisation inspirée du nombre d'or

**Statut : hypothèse exploratoire, pas une découverte.**

## Question
Un ordre de qubits déterministe dérivé de l'angle d'or peut-il réduire le nombre de coefficients d'une représentation MPS à fidélité contrôlée ?

Nous utilisons `phi=(1+sqrt(5))/2` et trions les qubits `i` par la partie fractionnaire de `i/phi`. Pour 8 qubits, on obtient `(0,5,2,7,4,1,6,3)`.

C'est une **heuristique arbitraire inspirée d'une suite quasi-périodique**. Aucun lien causal avec la géométrie des pyramides n'est présupposé.

## Expériences
Le programme `quantum_workspace_theorie_02_nombre_or.py` compare trois ordres : naturel, nombre d'or, information mutuelle. Il reprend les quatre états de référence de la théorie 01. Il exécute aussi 36 comparaisons entre l'ordre doré, l'ordre naturel et un ordre aléatoire, sur des états Ising brouillés (3 champs, 12 permutations par champ).

Fidélité minimale : **99,99 %**. Les quantités rapportées sont le nombre de coefficients MPS et la dimension des liaisons, **pas la RAM réelle ni la vitesse**.

## Résultats observés (8 qubits)

| État | Ordre initial | Nombre d'or | Information mutuelle |
| --- | ---: | ---: | ---: |
| Paires de Bell | 680 | 680 | 56 |
| GHZ | 56 | 56 | 56 |
| Ising 1D brouillé | 348 | 220 | 168 |
| État aléatoire | 680 | 648 | 648 |

Dans les 36 essais Ising : face à l'ordre initial, l'ordre doré fait mieux **12** fois, pareil **13**, moins bien **11** ; face à un ordre aléatoire, mieux **11**, pareil **10**, moins bien **15**. La moyenne des coefficients MPS est de 415,56 pour l'ordre doré, 423,89 pour l'ordre initial et 408,67 pour l'ordre aléatoire.

**Interprétation : aucune supériorité générale du nombre d'or n'est démontrée**. Les avantages des heuristiques géométriques doivent être comparés à des méthodes adaptées à la structure physique, notamment le regroupement par information mutuelle.

## Limites
- 8 qubits uniquement, état complet connu (coût exponentiel).
- Les ordres sont fixés avant les calculs, pas réadaptés pendant l'évolution.
- Ni temps d'exécution ni mémoire de pointe mesurés.
- La dimension maximale de liaison ou le nombre de coefficients ne suffit pas à prouver un gain de temps.
- Les 36 essais ne constituent pas des systèmes physiques indépendants : il s'agit de permutations de 3 états Ising.

## Suite de recherche
Tester des graphes inspirés de Fibonacci et des découpages hiérarchiques (arbres de tenseurs), face aux arbres équilibrés et à des algorithmes de partitionnement informés par les corrélations. Pré-enregistrer métriques et conditions de succès, et comparer sur des systèmes hors entraînement.

## Reproduction
```bash
python quantum_workspace_theorie_02_nombre_or.py
python quantum_workspace_tests_02.py
```
