# Pistes de recherche — Quantum Workspace X : au-delà des réorganisations MPS
**Revue exploratoire — 12 novembre 2026. Aucun résultat nouveau ni supériorité démontrés.**

## Position du projet
Nous conservons l'objectif initial : **réduire le coût de la simulation classique de systèmes quantiques** en choisissant intelligemment la représentation (MPS/TTN), la méthode d'application des opérateurs (SWAP/MPO/zip-up) et la précision, sans supposer un ordinateur quantique physique. Les travaux de « friction atomique » sont **hors périmètre** de cette feuille de route.

### Ce que la littérature a déjà établi
- Les géométries d'arbres de tenseurs peuvent être réorganisées selon l'intrication ; ce n'est pas une idée entièrement neuve. Travaux de visualisation et optimisation d'arbres : https://www.ueda-group.qiqb.osaka-u.ac.jp/publications/visualization-of-entanglement-geometry-by-structural-optimization-of-tree-tensor-network/
- Les méthodes par regroupement adaptatif de qubits sont déjà employées en simulation quantique : https://portal.fis.tum.de/en/publications/dynamical-cluster-based-strategy-for-improving-tensor-network-alg/
- Le zip-up MPO–MPS est une technique établie et souvent efficace, mais le contrôle strict de son erreur globale n'est pas automatique : https://tensornetwork.org/mps/algorithms/zip_up_mpo/
- Une hyperoptimisation coût/erreur pour contractions et compressions sur graphes arbitraires existe déjà : https://doi.org/10.1103/PhysRevX.14.011009
- L'adaptation des dimensions de liaison est étudiée, notamment avec contrôle PID lié à l'entropie : https://arxiv.org/abs/2604.03960
- Pour la chimie, l'optimisation des orbitales et la compression par hypercontraction sont des voies sérieuses : https://pmc.ncbi.nlm.nih.gov/articles/PMC12288016/

Cela exclut de présenter comme nouvelle **une simple utilisation** de MPS, TTN, MPO, zip-up, Fibonacci, regroupement, prédiction d'entropie ou choix de contraction.

## Hypothèse A — Ordonnanceur prudent à coût total calibré (priorité immédiate)
Laisser le simulateur choisir entre :
1. routage SWAP local ;
2. MPO direct (Théorie 09) ;
3. MPO appliqué par **zip-up** (Théorie 10, seulement après validation) ;
4. *ne pas réorganiser* ;
5. à plus long terme, changer de représentation MPS/TTN.

Pour chaque méthode m, estimer **sur une machine donnée** coût temporel T(m), mémoire de pointe M(m), erreur de troncature E(m), et coût de transition C(m). Le choix peut minimiser

`score(m) = T_hat(m) + lambda*M_hat(m) + mu*E_hat(m) + C_hat(m)`

**sous contraintes dures** `peak_RAM <= budget` et `error <= tolerance`. Les coefficients ne sont pas des constantes universelles et seront calibrés sur les objectifs de l'expérience.

**Nouveauté éventuelle :** une politique conservatrice de sélection en ligne, avec intervalle d'incertitude, qui passe à une méthode sûre si la prédiction est peu fiable et apprend *sans utiliser les opérations futures*. L'idée générale d'optimiser un choix par coût et contrainte n'est pas nouvelle : il faudra un gain reproducible et un mécanisme spécifique aux réseaux de tenseurs.

**Test décisif :** comparer sur les mêmes circuits au meilleur de (SWAP, MPO, zip-up, hybrid-budget, méthode de référence quimb/MQT YAQS). Comptabiliser la décision, les SVD/QR, le coût de transition et la RAM de pointe réelle.

## Hypothèse B — Changement de géométrie avec hystérésis
Explorer un graphe « interactions observées + estimations locales de troncature ». En fonction d'un score, conserver le MPS actuel, tester un autre ordre ou passer à une arborescence TTN. Réduire les oscillations par hystérésis : le bénéfice prédit doit dépasser **coût du changement + marge de sécurité**.

La topologie adaptative et l'information mutuelle existent déjà. Notre question devient le *coût amorti de changement et de surveillance*, qui avait pénalisé nos Théories 05–07.

## Hypothèse C — Deux représentations, décision locale, conversion exceptionnelle
MPS pour interactions linéaires/locales ; TTN quand des corrélations en groupes dominent ; MPO streaming pour interactions éloignées. Un méta-contrôleur n'effectue une conversion qu'après prédiction d'un avantage durable. Référence : évaluer aussi les arbres équilibrés, Fibonacci et guidés par l'intrication sans faire du nombre d'or une propriété physique.

**Attention :** « permuter virtuellement les étiquettes des qubits » sans transformer les tenseurs **n'est pas correct en général** ; des schémas de relabeling sans SWAP existent seulement sous des conditions ou symétries particulières : https://arxiv.org/abs/2607.08396

## Hypothèse D — Allocation globale d'erreur
Au lieu d'imposer partout le même `chi`, répartir une **enveloppe d'erreur numérique cumulée** entre opérations et régions ; déplacer le budget seulement après une estimation valable de l'erreur. Une somme de poids tronqués locaux **ne garantit pas toujours** un contrôle global sur une MPS non canonique. Validation avec références denses et observables physiques obligatoire.

## Protocole minimum
1. **Baselines honnêtes :** fixer `chi` et tolérance, puis égaliser la fidélité ou l'erreur observable ; noter quand l'égalité est impossible.
2. **Comparaison en aveugle :** entraînement/calibration sur quelques circuits ; évaluation sur familles, longueurs et graines non vues. Les circuits déterministes à graines différentes ne comptent pas comme expériences indépendantes.
3. **Mesures :** temps médian et dispersion, mémoire RSS de pointe en processus isolés, erreur de fidélité à n<=10, écarts d'observables au-delà, nombre et coûts de SVD, QR, SWAP, conversions et décisions.
4. **Ablations :** retirer l'estimation d'incertitude, l'hystérésis, le zip-up, le choix TTN et comparer au meilleur contrôle simple.
5. **Règle de réussite :** amélioration robuste sur *temps total ou mémoire de pointe* à **erreur comparable** et contre le meilleur contrôle simple établi ; rapporter les échecs.

## Prochaine expérience (Theory 11)
Commencer par une comparaison **SWAP vs MPO eager vs zip-up** sur les cas déjà reproduits de la Théorie 09. Apprendre sur un jeu de calibration les ordres de grandeur de coût à partir de (distance logique, dimensions de liaison locales, coefficient de MPO, limite de RAM, seuil de troncature). Tester ensuite une politique de sélection sans lecture d'opérations futures, sur des circuits tenus à l'écart.

Avant d'écrire une IA sophistiquée, tenter une régression robuste / heuristique analytique calibrée. Ne passer à un modèle ML que si le baseline ne suffit pas.

## Limite
Cette feuille de route identifie des **hypothèses testables** : elle n'établit ni découverte originale, ni amélioration mesurée, ni utilité médicale prouvée.
