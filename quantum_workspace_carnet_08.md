# Carnet de recherche 08 — Friction atomique et perturbation quantique mobile

**11 novembre 2026 — expérience calculée et vérifiée sur de petits systèmes.**  
**Statut : méthodes physiques connues, nouveaux exemples dans notre laboratoire ; pas une découverte scientifique.**

## Idée de départ

Étudier la **friction à l'échelle atomique** et l'absorption d'énergie pendant une perturbation mobile. Nous distinguons volontairement **deux problèmes physiques différents**.

### A. Friction classique d'une pointe (Prandtl–Tomlinson)

Une pointe de masse m est entraînée par un ressort de raideur k, dont le support se déplace à vitesse v. Le substrat exerce une force issue d'un potentiel périodique.

Équation de dynamique :

    m * d²x/dt² = k*(v*t - x) - dV_sub/dx - gamma*dx/dt

Le travail extérieur et la chaleur du terme visqueux sont suivis **pendant l'intégration** :

    W_ext = integral_0^T k*(v*t - x(t)) * v dt
    Q = integral_0^T gamma * (dx/dt)² dt

Le bilan nécessaire est **W_ext = variation d'énergie mécanique + Q**.

Nous testons deux substrats :
- périodique : V_sub = U*(1-cos(2*pi*x/a)) ;
- quasi-périodique : V_sub = U*(1-r)*(1-cos(2*pi*x/a)) + U*r*(1-cos(2*pi*x/(a*phi))) avec r=0,4 et phi=(1+sqrt(5))/2.

Le rapport du nombre d'or est ici **une hypothèse d'organisation des longueurs d'onde** déjà reliée à des études d'incommensurabilité ; nous n'en déduisons aucune propriété universelle.

**Attention au protocole :** les deux potentiels n'ont pas la même pente maximale ni la même distribution des barrières. Une variation de friction dans ce seul test **n'établit pas** une supériorité de Fibonacci, une superlubricité, ni un phénomène nouveau. Il faudra comparer des ensembles de phases, de vitesses et d'amplitudes normalisées.

### Résultats PT (unités sans dimension, k=4, gamma=1,5, U=1, distance=5, vitesse=0,22)

| Observables | Périodique | Quasi-périodique r=0,4 |
|---|---:|---:|
| Travail extérieur | 17,549096 | 13,133076 |
| Chaleur due à l'amortissement | 15,708232 | 10,716018 |
| Variation énergie mécanique (environ) | 1,840864 | 2,417058 |
| Erreur max du bilan énergétique | 1,53 × 10^-9 | 2,11 × 10^-9 |

Ces quantités dépendent fortement des paramètres choisis. Elles ne prouvent pas une réduction générale de la friction.

### B. Réponse d'une chaîne quantique (modèle de spins, PAS un modèle de frottement atomique)

Hamiltonien fermé :

    H(t) = -h * sum_i Z_i - J * sum_i Z_i Z_(i+1)
           + sum_i A_i(t) X_i

avec

    A_i(t) = A * sin²(pi*t/T) *
             exp[-(i - (n-1)*t/T)² / (2*sigma²)]

La perturbation transverse se déplace le long de la chaîne et s'annule aux temps 0 et T. L'état initial |00...0> est l'état fondamental du Hamiltonien H(0)=H(T) pour h,J>0.

Le moteur utilise un **MPS compressé** et une évolution de Trotter symétrique de second ordre, en réutilisant notre moteur de la théorie 04. La comparaison indépendante utilise une **intégration de Schrödinger en espace complet** par exponentielle sparse avec la valeur du Hamiltonien au milieu du pas. C'est une référence indépendante **discrétisée**, et non une solution analytique exacte du problème dépendant du temps.

L'observable est

    Travail absorbé = <psi(T)|H(0)|psi(T)> - énergie fondamentale

**Ce n'est pas de la chaleur dissipée** : le système quantique fermé conserve une évolution réversible, et aucune interaction explicite avec un bain n'a été modélisée. La carte locale montre p_i=(1-<Z_i>)/2, une probabilité de spin inversé, **pas une image d'atomes réels**.

### Résultat : 6 spins, h=1, J=0,45, A=1,1, largeur=0,85, T=1,8

- Pas de Trotter : dt=0,03.
- Dimension de liaison maximale : chi=8.
- Travail absorbé après le passage : **1,579283** unités de simulation.
- Fidélité finale contre la référence sparse midpoint : **0,999999947**.
- Nombre maximal de coefficients des tenseurs MPS : **104**.
- Contrôle sans excitation (A=0) : **travail absorbé ≈ 0**.

Cette fidélité ne valide que ce petit cas précis ; l'erreur sur le travail est une autre métrique, à mesurer séparément.

### Convergence numérique (6 spins, T=1,8)

| dt | chi | Fidélité à la référence sparse midpoint | Travail MPS |
|---:|---:|---:|---:|
| 0,09 | 8 | 0,99999549 | 1,558944 |
| 0,06 | 8 | 0,99999922 | 1,572232 |
| 0,03 | 8 | 0,99999995 | 1,579283 |

Ces valeurs sont une vérification **de notre implémentation**, et non une démonstration d'une nouvelle méthode de simulation quantique.

## Exécution et vérifications

Depuis la racine du dépôt :

    python -m pip install -r requirements.txt
    python quantum_workspace_tests_08.py
    python quantum_workspace_experience_08_friction.py --n 6 --chi 8 --dt 0.03

Le programme génère un rapport JSON et, si Matplotlib est disponible, une carte PNG des excitations locales.

Les tests valident :
1. bilan d'énergie classique, amortissement nul et potentiel quasi-périodique ;
2. fidélité du MPS contre le propagateur sparse pour 6 et 8 spins ;
3. absence de transfert d'énergie si la perturbation est nulle ;
4. stabilité des observables même après réorganisation des qubits ;
5. convergence de la fidélité quand on raffine le pas temporel.

## Suites de recherche crédibles

1. **Rendre la comparaison des surfaces équitable :** balayages en phase, vitesse et amplitude, normalisation des pentes et des barrières, métriques d'énergie et stick–slip.
2. **Ajouter une chaîne phononique au modèle de friction :** un vrai transfert d'énergie à des modes vibratoires, plutôt qu'une force de dissipation ad hoc.
3. **Étudier un modèle quantique ouvert :** un bain d'oscillateurs ou Lindblad, avec bilan des flux de chaleur ; la chaîne de spins fermée n'est pas suffisante.
4. **Améliorer le moteur de calcul :** comparer notre TEBD à quimb/TeNPy, mesurer temps, RAM et erreur sur des ensembles hors mise au point et des tailles croissantes.
5. **Tester une politique de compression basée sur l'énergie locale :** mettre la précision là où le passage de la perturbation génère des excitations, en mesurant les économies *à erreur égale*.

## Sources scientifiques existantes

- Popov, **Prandtl–Tomlinson model: History and applications in friction, plasticity, and nanotechnologies**, ZAMM (2012), https://doi.org/10.1002/zamm.201200097
- Wang et al., **Energy dissipation of atomic-scale friction based on one-dimensional Prandtl–Tomlinson model**, Friction (2015), https://doi.org/10.1007/s40544-015-0086-2
- Krylov & Frenken, **Atomistic mechanisms for frictional energy dissipation during continuous sliding**, Scientific Reports (2021), https://doi.org/10.1038/s41598-021-99437-z
- Tensor Network, **Time-evolving block-decimation (TEBD)**, https://tensornetwork.org/mps/algorithms/timeevo/tebd.html
- ITensorMPS, **MPS Time Evolution** (documentation), https://docs.itensor.org/ITensorMPS/stable/tutorials/MPSTimeEvolution.html

**Aucune preuve de nouvelle physique, de superlubricité, de suprématie quantique ou d'effet médical n'a été obtenue.**
