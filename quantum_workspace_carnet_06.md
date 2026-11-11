# Quantum Workspace X — Carnet de recherche 06

**11 novembre 2026 — Expérience sur l'observation quantique sélective**

**Statut : prototype testé sur 8 et 10 qubits, aucune découverte nouvelle ni supériorité générale démontrée.**

## Question de recherche

Une politique MPS peut-elle décider **quand observer des corrélations et quelles paires examiner**, plutôt que d'évaluer l'information mutuelle de toutes les paires après chaque lot de portes ?

Cette expérience teste un mécanisme prudent : si deux lots d'interactions consécutifs ont les mêmes paires, on échantillonne au plus `budget` corrélations via contractions MPS (pas de reconstruction dense) ; on ne réorganise la chaîne que si l'information mutuelle échantillonnée dépasse un seuil et si un gain de routage fondé sur l'historique est attendu.

**Crucial : le contrôleur ne lit jamais les interactions futures.** Il apprend seulement celles des lots déjà exécutés. Les interactions de la simulation sont **synthétiques**, non des mesures de systèmes physiques.

## Dépendances et théorie

- Q04 : représentation MPS avec opérations à 1 ou 2 qubits, SVD locale et routage par SWAP.
- Q05 : diagnostic complet des corrélations depuis le MPS, contrôle `history`, `history_confident`, `reactive`.
- Q06 : échantillonnage de quelques paires `pair_mi` après des lots jugés stables.

L'information mutuelle `I(A:B) = S(A) + S(B) - S(AB)` mesure **l'ensemble des corrélations quantiques ET classiques**, pas uniquement l'intrication. Le calcul de matrices réduites via MPS est standard. Voir [revue MPS / évolution temporelle (Paeckel et al., 2019)](https://doi.org/10.1016/j.aop.2019.167998) et [revue des algorithmes réseaux de tenseurs](https://doi.org/10.1146/annurev-conmatphys-040721-022705).

## Comparaison / protocole

Stratégies :
- `fixed` : ordre original, sans adaptation ;
- `history` : adaptation selon les interactions de la dernière étape, sans diagnostic MI ;
- `history_confident` : adaptation après deux motifs historiques identiques, sans MI ;
- `reactive` : calcul de **toutes** les paires MI après chaque étape, adaptation sur leur carte ;
- `selective` : au plus 3 ou 4 paires MI par diagnostic déclenché, adaptation conditionnelle.

Trois scénarios : motifs répétitifs, motifs changeants, motifs aléatoires. Les **motifs répétitifs et changeants sont déterministes** d'une graine à l'autre ; seules les interactions du scénario aléatoire varient avec la graine. Répéter ces scénarios avec six graines ne constitue donc pas six circuits indépendants.

Les temps incluent diagnostic, décision, reconfiguration et évolution MPS, **mais ne constituent pas un benchmark sur matériel dédié ou sur environnement stabilisé**. La précision est évaluée par rapport à une référence de vecteur d'état dense **seulement pour n <= 10**.

### 8 qubits, chi=16, 12 lots, six graines (11,12,13,14,15,31)

| Scénario | Stratégie | SWAP moyens | Temps moyen (ms) | Paires MI échantillonnées, en moyenne |
| --- | --- | ---: | ---: | ---: |
| Répétitif | Fixe | 288 | 74,7 | 0 |
| Répétitif | Historique | **66** | **23,3** | 0 |
| Répétitif | MI complète | **66** | 420,2 | toutes |
| Répétitif | Sélective | 114 | 49,1 | 12 |
| Changeant | Fixe | 192 | 49,2 | 0 |
| Changeant | Historique | **76** | **25,4** | 0 |
| Changeant | MI complète | 162 | 497,6 | toutes |
| Changeant | Sélective | 168 | 55,7 | 9 |
| Aléatoire | Fixe | 210,7 | 62,9 | 0 |
| Aléatoire | Historique | 258 | 74,5 | 0 |
| Aléatoire | MI complète | 211,2 | 719,3 | toutes |
| Aléatoire | Sélective | 211 | 73,7 | 0,5 |

La fidélité finale est proche de **1** dans ces petits cas à `chi=16` ; cela ne démontre aucune généralisation à des systèmes plus complexes.

### 10 qubits, chi=16, neuf lots, deux graines (11,23)

La troncature MPS entraîne des erreurs non négligeables selon l'ordre, ce qui rend une simple comparaison du nombre de SWAP **injuste**. Exemples de fidélité :

| Scénario | Fixe | Historique | Sélective |
| --- | ---: | ---: | ---: |
| Répétitif | 0,1012 | 0,9132 | 0,6269 |
| Changeant | 0,2571 | 0,7121 | 0,3634 |
| Aléatoire | 0,6997 | 0,6776 | 0,6997 |

Ces résultats **ne doivent pas être interprétés comme un avantage quantique**.

### 10 qubits, chi=32, neuf lots, deux graines

La fidélité de toutes les stratégies revient à environ 1 dans nos tests (erreur numérique négligeable). Le surcoût de l'observation sélective persiste.

| Scénario | Fixe (ms) | Historique (ms) | MI complète (ms) | Sélective (ms) |
| --- | ---: | ---: | ---: | ---: |
| Répétitif | 115,6 | **35,9** | 879,2 | 103,3 |
| Changeant | 85,4 | **36,3** | 1 017,8 | 180,1 |
| Aléatoire | 84,2 | 99,9 | 1 528,0 | 117,0 |

## Conclusion honnête

**Succès limité :** sur ces exemples, échantillonner quelques paires est bien moins coûteux que calculer la carte MI entière. Nous avons vérifié la fidélité sur les petits systèmes et le fait que modifier le dernier lot ne change pas les décisions sur le préfixe commun.

**Échec de l'hypothèse forte à ce stade :** la stratégie sélective n'est pas meilleure que la stratégie simple fondée uniquement sur l'historique. Elle utilise souvent davantage de SWAP, de temps et de mesures. Le déclenchement sur les motifs stables peut être redondant puisque l'historique suffit déjà.

**Ce qu'on n'a pas démontré :** réduction de RAM réelle, gains généralisables, meilleure précision à budget égal, originalité algorithmique, simulation utile en médecine.

## Pistes crédibles pour la théorie 07

1. Exploiter les **spectres singuliers déjà calculés par la SVD**, au lieu de recontracter le MPS : un diagnostic de croissance de complexité presque gratuit à certains instants.
2. Observer seulement quand une **incertitude de décision** le justifie (changement de régime, troncature qui augmente, prévision instable), plutôt que lorsqu'un motif est stable.
3. Tenir une **comptabilité en unités de temps** : coût de l'observation + conversion des tenseurs + application des portes, avec coût de mémoire mesuré.
4. Comparer sur des circuits tenus à l'écart de la mise au point, plusieurs longueurs et mêmes seuils de fidélité. Répéter les mesures temporelles et publier la dispersion.

## Exécution

```bash
python -m pip install -r requirements.txt
python quantum_workspace_tests_06.py
python quantum_workspace_theorie_06_observation_selective.py --n 8 --chi 16 --repeats 4 --seeds 11 12 13 14 15 31 --budget 3
python quantum_workspace_theorie_06_observation_selective.py --n 10 --chi 32 --repeats 3 --seeds 11 23 --budget 4
```

Le programme sauvegarde les détails des résultats, y compris les décisions, les temps et les observations, dans `quantum_workspace_resultats_06_n*.json`.

## Limites reproductibles et validation

Les tests vérifient la MI échantillonnée contre la matrice MI complète, même après réorganisation des qubits, l'absence d'accès au futur (test de préfixe commun), un plafond de paires par diagnostic, et la fidélité à la référence exacte de huit qubits. Les exécutions à `n>10` ne fournissent **pas** de fidélité indépendante.
