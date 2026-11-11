# Carnet de recherche 04 — Routage anticipatif sur un MPS compressé

**Date : 11 novembre 2026**  
**Statut : prototype numérique, méthodes de base connues, aucune découverte démontrée.**

## Question de recherche

Une représentation MPS peut-elle réduire le coût de certaines simulations lorsqu'un moteur connaît **les interactions qui vont être appliquées** et réorganise les qubits avant leur exécution ?

**Ce travail teste le routage des interactions futures déjà connues, PAS la prédiction de l'intrication.**

## Méthode

Le programme `quantum_workspace_theorie_04_predictive_mps.py` :

- maintient l'état quantique dans une chaîne de tenseurs MPS ;
- applique les rotations à un qubit et des portes `exp(-iθ Z⊗Z)` ;
- effectue les interactions éloignées à l'aide de SWAP, en conservant la correspondance des qubits logiques ;
- compresse après chaque opération à deux qubits avec une SVD, un plafond de liaison `chi` et un seuil de troncature ;
- compare l'état final à une référence dense indépendante lorsque `n <= 10` ;
- compte les SWAP de routage et de réorganisation, les SVD, les coefficients de tenseurs au maximum et des temps CPU.

Les cinq politiques :
1. `natural` : ordre des qubits fixe ;
2. `golden` : ordre initial quasi-périodique inspiré du nombre d'or ;
3. `compiled_static` : un ordre initial choisi à partir de **tout** le circuit (contrôle hors-ligne) ;
4. `reactive` : réorganisation d'après les paires d'interactions de l'étape précédente ;
5. `lookahead` : réorganisation d'après les paires d'interactions **de l'étape suivante, déjà connues**.

Le coût du calcul des choix de routage et de l'ordre statique est inclus dans le chronométrage du programme. Les temps restent des mesures isolées, soumises à la machine et au bruit, **pas** une preuve de vitesse supérieure.

## Résultat 8 qubits, chi=16, passes=4

| Politique | SWAP au total | SVD | Coefficients MPS maximum | Fidélité exacte |
| --- | ---: | ---: | ---: | ---: |
| Ordre naturel | 192 | 240 | 680 | ~1,000000 |
| Nombre d'or | 224 | 272 | 680 | ~1,000000 |
| Statique compilé | 128 | 176 | 680 | ~1,000000 |
| Réactif | 232 | 280 | 680 | ~1,000000 |
| Anticipatif | **20** | **68** | **680** | ~1,000000 |

**Interprétation :** moins de SWAP/SVD, mais **pas** d'économie sur le nombre maximal de coefficients stockés à 8 qubits.

## Résultat 10 qubits, chi=16, passes=4

| Politique | SWAP au total | SVD | Coefficients MPS maximum | Fidélité exacte |
| --- | ---: | ---: | ---: | ---: |
| Ordre naturel | 320 | 380 | 1 704 | 0,1423 |
| Nombre d'or | 208 | 268 | 1 704 | 0,7653 |
| Statique compilé | 192 | 252 | 1 704 | 0,3123 |
| Réactif | 385 | 445 | 1 704 | 0,3123 |
| Anticipatif | **33** | **93** | **1 192** | ~1,000000 |

La fidélité est `|<ψ_exact|ψ_MPS>|² / (||ψ_exact||² ||ψ_MPS||²)`.

Sur ce circuit structuré, la stratégie anticipative réduit le nombre formel maximal de coefficients MPS d'environ **30 %** et conserve une fidélité proche de 1. Les autres politiques troncaturent davantage à `chi=16` : **comparer uniquement le nombre de coefficients sans mentionner leurs erreurs serait trompeur**. En portant `chi` à 32, toutes les stratégies du cas 10 qubits approchent la fidélité 1, mais la stratégie anticipative reste la plus compacte pour cette instance.

Le programme de recherche est **expérimental et éducatif** : il n'est pas optimisé comme les bibliothèques MPS établies. Une simple stratégie sachant à l'avance les interactions d'un circuit bien structuré peut être favorisée par la conception du circuit.

## Limitations essentielles

- **Pas de prédiction quantique :** seules les interactions du circuit à venir sont exploitées, pas des observations physiques apprises.
- Les circuits sont synthétiques, réguliers et prédéfinis ; le résultat peut ne pas se généraliser.
- La SVD locale est une technique classique bien connue.
- Les coefficients MPS ne sont **pas** la RAM de pointe ; le programme comptabilise séparément la taille de la matrice SVD mais ne mesure pas toute la mémoire temporaire.
- Les temps muraux sur un seul lancement sont insuffisants pour démontrer une accélération ; il faudra plusieurs graines, tailles et répétitions.
- La fidélité indépendante n'est calculée que jusqu'à 10 qubits. Au-dessus, une fidélité élevée n'est **pas** établie.

## Reproduire

Depuis la racine du dépôt :

```bash
python -m pip install -r requirements.txt
python quantum_workspace_tests_04.py
python quantum_workspace_theorie_04_predictive_mps.py --n 8 --chi 16
python quantum_workspace_theorie_04_predictive_mps.py --n 10 --chi 16
python quantum_workspace_theorie_04_predictive_mps.py --n 10 --chi 32
```

Chaque exécution enregistre les données JSON dans un fichier `quantum_workspace_resultats_04_n*_chi*.json`.

## La prochaine vraie hypothèse

**H5 : estimation de la croissance des corrélations à partir du MPS courant**, sans connaissance du circuit futur, permettant de choisir un changement de représentation seulement si le gain estimé dépasse la somme de tous les coûts : estimation, transfert, SVD, reconstruction et erreur.

Protocole H5 : circuits non structurés, benchmarks de référence MPS/TTN, graines de test hors entraînement, courbes erreur/RAM/temps, coût de décision inclus, rapport systématique des échecs. Une amélioration unique sur un circuit choisi ne suffira pas à démontrer une découverte.