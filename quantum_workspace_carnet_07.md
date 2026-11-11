# Quantum Workspace X — Carnet de recherche 07

**Date : 11 novembre 2026**  
**Statut : résultat négatif contrôlé, prototype reproductible ; aucune découverte nouvelle revendiquée.**

## 1. Problème et hypothèse

Les expériences 05–06 ont montré que la mesure de l'information mutuelle (MI) devient parfois plus coûteuse que la simulation elle-même. Nous essayons une politique H7 :

> N'observer que lorsqu'un changement du motif d'interactions passé coïncide avec un diagnostic numérique de compression MPS défavorable ; sinon s'abstenir.

Notre politique ne lit **jamais** la prochaine porte au moment de décider. Elle exploite uniquement les interactions précédentes, les dimensions des tenseurs MPS, et le poids relatif cumulé des valeurs singulières écartées lors de la SVD.

**Attention :** la dimension d'une liaison et le poids écarté ne sont **pas une mesure de l'intrication** dans une MPS de jauge quelconque. Il faut obtenir une forme canonique et des spectres de Schmidt pour interpréter des entropies physiques. Pour cette raison nous les appelons des *signaux numériques de risque*, pas des spectres d'intrication.

## 2. Ce que nous réutilisons de la recherche

| Outil / méthode existante | Utilité pour notre projet | Ce qu'il ne faut pas réinventer |
| --- | --- | --- |
| [quimb CircuitMPS](https://quimb.readthedocs.io/en/latest/circuit/circuit-mps.html) | Simulation MPS Python, portes non locales, intégration possible GPU | Routines standard de portes, contraction et troncature |
| [TeNPy](https://tenpy.readthedocs.io/en/latest/reference/tenpy.networks.mps.MPS.html) | MPS canoniques, Schmidt et contrôle de troncature | Canonicalisation correcte et interprétation des spectres |
| [ITensorMPS](https://docs.itensor.org/ITensorMPS/stable/MPSandMPO.html) | Référence de calcul scientifique à plus grande échelle | Réorganisation de jauge et dimension de liaison |
| [Qiskit Aer](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html) | Simulateur de référence indépendant, mode MPS et journaux de troncature | Implémentation de base d'un simulateur de circuits |
| [Contrôle PID de dimension de liaison, prépublication 2026](https://arxiv.org/abs/2604.03960) | Comparaison scientifique pour une adaptation temporelle | Ne pas présenter l'adaptation PID/EMA comme nouvelle |

**Stratégie d'ingénierie :** garder l'implémentation NumPy *minimale* pour l'audit et les tests, vérifier les états sur un moteur quimb indépendant, puis migrer si nos métriques justifient le coût de la migration. Quimb est une référence de validation optionnelle : le code de production du prototype n'utilise pas encore son moteur pour les politiques de routage.

## 3. Protocole

Scripts : [contrôleur 07](quantum_workspace_theorie_07_budget.py), [tests causaux](quantum_workspace_tests_07.py), [validation quimb optionnelle](quantum_workspace_validation_quimb.py).

**Comparateurs obligatoires :**
- ordre fixe ;
- historique seul (baseline forte de 05) ;
- historique avec confirmation de stabilité ;
- observation conditionnelle avec budget de 2 paires.

Trois types de circuits synthétiques : motifs répétitifs, changements de régime et appariements aléatoires. À la différence de 05–06, chaque graine permute les identifiants logiques même dans les scénarios répétitifs et changeants. Cela diversifie les distances de routage ; **ce n'est pas un nouveau modèle physique indépendant**.

**Critères :** fidélité à un calcul dense indépendant pour 8 et 10 qubits, nombre total de SWAP, SVD, taille formelle maximale des tenseurs, durée murale *qui inclut les observations et transformations*. Le suivi de la RAM du processus (NumPy et allocations temporaires compris) reste à implémenter dans un banc d'essai isolé.

Les temps ci-dessous sont les **médianes d'une exécution par graine sur une machine Python**. Ils ne sont pas des mesures matérielles stables ou une preuve statistique de vitesse. Les six graines 8 qubits sont 17, 23, 29, 31, 37, 41 ; pour 10 qubits : 17, 23, 29.

## 4. Résultats locaux à 8 qubits, chi=16 (9 lots, 6 graines)

| Scénario | Fixe | Historique | Historique confirmé | Budgeté |
| --- | ---: | ---: | ---: | ---: |
| Répétitif | 30,8 ms | **14,6 ms** | 21,5 ms | 17,2 ms |
| Changeant | 28,8 ms | **23,5 ms** | 34,9 ms | 38,4 ms |
| Aléatoire | **38,2 ms** | 48,2 ms | 39,2 ms | 53,1 ms |

Tous les états finaux sont reproduits avec une fidélité proche de 1 dans la précision numérique.

## 5. Résultats locaux à 10 qubits, chi=32 (9 lots, 3 graines)

| Scénario | Fixe | Historique | Historique confirmé | Budgeté |
| --- | ---: | ---: | ---: | ---: |
| Répétitif | 55,1 ms | **21,9 ms** | 33,7 ms | 36,2 ms |
| Changeant | 73,5 ms | **34,0 ms** | 51,2 ms | 58,9 ms |
| Aléatoire | 103,1 ms | 98,5 ms | **73,7 ms** | 114,1 ms |

Toutes les stratégies conservent ici également une fidélité proche de 1.

## 6. Interprétation

**L'hypothèse forte échoue sur notre banc d'essai :** notre déclenchement sélectif a moins de frais que l'observation complète, mais ne bat pas la meilleure stratégie simple. La **réorganisation sous incertitude** est davantage le problème que la mesure de corrélations.

Les résultats ne démontrent pas de diminution de RAM, de supériorité à grande échelle, de découverte en chimie quantique ou d'intérêt médical.

Notre prochaine étape n'est donc **pas** de multiplier les heuristiques ou de louer 1 000 GPU, mais de :
1. remplacer la mesure MI coûteuse par des métriques canoniques validées avec TeNPy/quimb ;
2. tester la politique dans des circuits où l'historique seul est insuffisant, sans ajuster les seuils sur les données de test ;
3. mesurer la RAM et la latence sur des exécutions répétées en processus séparés ;
4. valider l'évolution vers 12–20 qubits avec un backend MPS scientifique (sans reconstruction dense) et vérifier des observables physiques ;
5. introduire un modèle de chimie simple (par exemple chaîne de Hubbard ou petites molécules) avant de parler de médecine.

## 7. Reproduction

Depuis la racine du dépôt :

~~~bash
python -m pip install -r requirements.txt
python quantum_workspace_tests_07.py
python quantum_workspace_theorie_07_budget.py --n 8 --chi 16 --repeats 3 --seeds 17 23 29 31 37 41 --budget 2
python quantum_workspace_theorie_07_budget.py --n 10 --chi 32 --repeats 3 --seeds 17 23 29 --budget 2
~~~

Un fichier quantum_workspace_resultats_07_n8.json ou n10.json est créé localement, contenant le détail des décisions et mesures. Pour une validation externe :

~~~bash
python -m pip install -r requirements-reference.txt
python quantum_workspace_validation_quimb.py
~~~

## 8. Ce qui serait une vraie contribution

Une méthode qui réduit **la durée totale ou la RAM réelle à erreur égale** face à un moteur quimb/TeNPy/ITensor bien paramétré, sur des modèles physiques de taille croissante, avec un protocole reproductible et une comparaison à des travaux scientifiques publiés.

La possibilité reste ouverte, mais aucun avantage de ce type n'est démontré à ce jour par nos expériences.
