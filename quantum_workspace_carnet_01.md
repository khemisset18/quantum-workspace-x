# Quantum Workspace X — Carnet de recherche n° 1

**Date :** 11 novembre 2026  
**Objet :** théorie 1 — la carte de l'intrication comme guide du calcul.  
**Statut :** premier prototype expérimental. **Aucune découverte nouvelle démontrée.**

## 1. Notre question

Peut-on réduire la mémoire nécessaire pour simuler un état quantique en plaçant
les qubits fortement corrélés près les uns des autres dans une représentation
par **états de produits de matrices (MPS)** ?

Les MPS compressent certains états quantiques en factorisant leurs amplitudes
avec des décompositions en valeurs singulières (SVD). Leur coût dépend fortement
de la dimension des liaisons entre tenseurs.

**Hypothèse expérimentale :** minimiser un coût fondé sur l'information mutuelle
quantique entre paires de qubits réduira souvent la dimension de liaison requise
pour une fidélité fixée. Cette idée de réorganisation est **déjà connue** dans
les réseaux de tenseurs et la méthode DMRG ; nous la validons avant d'imaginer
une variante originale et prédictive.

## 2. Méthode

- Simuler 8 qubits, soit un vecteur de 256 amplitudes complexes.
- Calculer pour chaque paire de qubits l'information mutuelle quantique :
  **I(i:j) = S(i) + S(j) − S(i,j)** où S est l'entropie de von Neumann (base 2).
- Chercher l'ordre des 8 qubits qui minimise :
  **C(ordre) = somme_(i<j) I(i:j) × distance_dans_la_chaîne(i,j)**.
- Pour l'ordre initial et le meilleur ordre, faire des SVD successives en gardant
  au plus D valeurs singulières à chaque coupure.
- Mesurer la fidélité de l'état reconstruit : **F = |⟨ψ|φ⟩|²** avec états normalisés.
- Trouver le plus petit D permettant F >= **0,9999**.
- Compter le nombre de coefficients complexes stockés dans les tenseurs MPS ;
  ce n'est **pas une mesure de temps GPU ni de RAM réelle du programme**.

L'optimisation de l'ordre est **exhaustive uniquement à 8 qubits** (40320
permutations, réduites de moitié en utilisant la symétrie du retournement). Cette
stratégie n'est pas extensible telle quelle à 1 000 GPU ou à de grandes molécules.

## 3. Résultats calculés

| Système simulé | Dimension de liaison avant | Après | Coefficients MPS avant → après | Commentaire |
|---|---:|---:|---:|---|
| 4 paires de Bell | 16 | 2 | 680 → 56 | Exacte dans les deux cas |
| État GHZ | 2 | 2 | 56 → 56 | Aucune amélioration |
| Ising 1D, ordre brouillé | 7 | 4 | 348 → 168 | Fidélité >= 99,99 % |
| État complexe aléatoire | 16 | 15 | 680 → 648 | Gain faible |

**Interprétation :** les états disposant d'une structure exploitable peuvent se
compresser beaucoup mieux grâce à un bon ordre. Une méthode qui marche sur un
état facile (paires de Bell) ne résout pas automatiquement les états quantiques
fortement intriqués ou des molécules réelles.

## 4. Ce qui n'est pas démontré

1. **Nouveauté** : la stratégie « information mutuelle + réordonnancement MPS »
   existe déjà dans la littérature.
2. **Avantage de calcul** : nous avons mesuré des dimensions et le nombre de
   coefficients des tenseurs, **pas** un gain réel de vitesse sur GPU.
3. **Passage à grande échelle** : notre code calcule d'abord l'état complet et
   la carte d'intrication exacte. Ces opérations coûtent déjà une mémoire qui
   augmente exponentiellement avec le nombre de qubits. Ce prototype ne
   contourne pas cette difficulté.
4. **Médecine** : nous n'avons simulé ni protéine ni traitement médical.

## 5. Première piste vers une innovation

**Hypothèse H2 — réorganisation prédictive, économique et vérifiable**

Plutôt que calculer une carte complète de l'intrication à chaque étape :

1. Estimer seulement quelques corrélations locales directement depuis une MPS
   ou depuis un petit nombre de mesures approximatives.
2. Prévoir quelles liaisons MPS vont croître lors de la prochaine étape d'une
   évolution quantique.
3. Décider de réorganiser les qubits **uniquement si le coût prédit de la
   simulation évitée dépasse le coût du déplacement et de la prédiction**.
4. Après chaque réorganisation, mesurer l'erreur, la mémoire et le temps total.
5. Comparer avec de vrais baselines : ordre fixe, ordre optimisé statique,
   méthodes MPS récentes, et borne supérieure sur le coût de l'algorithme.

Des travaux ont déjà abordé la réorganisation et la prévision de l'intrication.
La nouveauté reste **à rechercher** par analyse bibliographique et expériences
comparatives rigoureuses.

## 6. Prochaine expérience

Simuler une évolution d'un modèle d'Ising de 8 à 12 qubits sur plusieurs pas de
temps. Comparer une représentation fixe, une représentation réordonnée à chaque
pas, et une représentation qui ne réordonne que quand un gain est prédit.
Mesurer **temps de calcul complet, mémoire maximale, fidélité et coût des
réorganisations**. Utiliser plusieurs graines aléatoires et plusieurs modèles.

## 7. Fichiers

- `quantum_workspace_theorie_01.py` : programme complet.
- `quantum_workspace_tests_01.py` : tests de cohérence.
- `quantum_workspace_resultats_02.json` : résultats numériques reproductibles.
- `quantum_workspace_comparaison_02.png` : comparaison des dimensions MPS.
- `quantum_workspace_carte_intrication_02.png` : carte de corrélations Ising.

**Pour reproduire :**

```bash
python -m pip install numpy scipy matplotlib
python quantum_workspace_tests_01.py
python quantum_workspace_theorie_01.py
```

## 8. Références

- Mazen Ali (2021), *On the Ordering of Sites in the Density Matrix Renormalization Group using Quantum Mutual Information*, https://arxiv.org/abs/2103.01111
- ITensor, *Matrix Product States*, https://itensor.org/docs.cgi?page=tutorials/MPS
- ITensor, *Tensor Decompositions*, https://www.itensor.org/docs.cgi?page=classes/decomp
- ITensor, *Computing the Entanglement Entropy of an MPS*, https://github.com/ITensor/ITensorMPS.jl/blob/main/docs/src/examples/MPSandMPO.md