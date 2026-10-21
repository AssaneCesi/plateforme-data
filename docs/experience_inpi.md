# Expérience INPI : version CV
 
> **Mode d'emploi.** Copie la version A dans le CV Qualité / Gouvernance, la version B dans le CV Data Engineer.
> Remplace chaque `[crochet]` par un chiffre vérifié. Rien d'inventé, rien de confidentiel.
 
---
 
## 1. Ce que ton poste montre vraiment
 
L'intitulé dit « diffusion », mais ton travail réel est plus rare, et plus vendeur :
 
| Pilier | Ce que tu fais | Ce que le recruteur entend |
|---|---|---|
| **Run de la qualité** | Tickets GLPI et CCI, synchronisations RNE / greffes / Insee / data.inpi, anonymisations | Gestion d'incidents qualité, réconciliation inter-sources, RGPD |
| **Corrections de masse** | Scripts Python, PySpark, MongoDB sur des millions de SIREN | Traitements de données en production, à grande échelle |
| **Diagnostic** | Erreurs 500 dues aux uid qui changent | Analyse de cause racine, intégrité référentielle |
 
Peu de profils juniors peuvent dire « j'ai corrigé plusieurs millions d'enregistrements en production ». C'est ton argument principal, sur les deux CV.
 
---
 
## 2. En-tête de l'expérience
 
```
INPI, Institut national de la propriété industrielle          Avril 2025 – aujourd'hui
Chargé de diffusion de données (qualité et traitement du RNE)
Registre national des entreprises : registre unique des entreprises françaises,
alimenté par le Guichet unique des formalités.
```
 
Garde l'intitulé officiel (il sera vérifié) ; la parenthèse et la ligne de contexte disent ce que tu fais vraiment.
 
---
 
## 3. Version A : CV Qualité, gouvernance, Data Manager
 
- **Incidents qualité** : traitement de [plusieurs milliers] de tickets de qualité des données transmis par les partenaires de l'INPI et un cabinet de mandataires (exactitude des informations, radiations erronées, demandes d'anonymisation).
- **Réconciliation inter-sources** : correction des désynchronisations entre le RNE, les greffes, le répertoire Sirene de l'Insee et la diffusion open data (data.inpi.fr).
- **Corrections de masse** : harmonisation des règles de gestion entre le Guichet unique et le RNE sur [plusieurs millions] de SIREN ; suppression des doublons d'identifiants de représentants sur [plusieurs centaines de milliers] d'entreprises.
- **Conformité et référentiels** : mise en conformité structurelle de [plusieurs centaines de milliers] de sociétés étrangères ; intégration de la nomenclature d'activité artisanale NAFA 2025.
- **Analyse de cause racine** : diagnostic d'une rupture d'intégrité entre formalités et registre (identifiants modifiés entre le brouillon et le dépôt), [plusieurs milliers] de dépôts débloqués.
*Environnement : Python, PySpark, MongoDB, SQL, API Sirene de l'Insee.*
 
---
 
## 4. Version B : CV Data Engineer
 
- **Traitements de masse en production** sur le RNE (documents JSON sous MongoDB) en Python, PySpark et MQL : [plusieurs millions] de SIREN mis en cohérence avec les règles du Guichet unique.
- **Dédoublonnage** des identifiants de représentants sur [plusieurs centaines de milliers] d'entreprises ; **mise en conformité de schéma** de [plusieurs centaines de milliers] de sociétés étrangères.
- **Migration de nomenclature** : intégration du code d'activité NAFA 2025 dans les documents JSON des entreprises du RNE ([volume]).
- **Intégration de l'API Sirene** de l'Insee pour réconcilier le RNE avec le répertoire de référence.
- **Diagnostic d'erreurs de traitement** (HTTP 500) causées par des identifiants instables entre documents JSON ; [plusieurs milliers] de formalités débloquées.
*Environnement : Python, PySpark, MongoDB (MQL), SQL (DBeaver), API REST.*
 
---
 
## 5. Accroches mises à jour
 
**CV A**
> Data engineer (CESI, 2024) spécialisé dans la qualité des données. À l'INPI, je traite la qualité du Registre national des entreprises en production : [plusieurs milliers] d'incidents résolus avec les partenaires, [plusieurs millions] d'enregistrements corrigés par traitements de masse.
 
**CV B**
> Data engineer (CESI, 2024). À l'INPI, j'exécute en production des traitements de masse sur le Registre national des entreprises (Python, PySpark, MongoDB) : [plusieurs millions] de SIREN corrigés, avec la qualité et la conformité des données comme fil conducteur.
 
---
 
## 6. Chiffres à consolider
 
Un chiffre précis inspire plus confiance qu'un « plusieurs ». Préfère « 2,4 M » à « plusieurs millions » ; si le chiffre exact ne peut pas sortir, écris « plus de 2 M ».
 
| Réalisation | Ce que tu as | À préciser | Source probable |
|---|---|---|---|
| Erreurs 500 (uid) | plusieurs milliers | nombre, période, délai moyen de résolution | suivi des tickets |
| Tickets GLPI | plusieurs milliers | nombre, répartition par type | export GLPI |
| Demandes du cabinet de mandataires | quelques centaines | nombre | suivi des demandes |
| Harmonisation Guichet unique / RNE | plusieurs millions de SIREN | nombre exact, part du registre | journaux des scripts |
| Sociétés étrangères | plusieurs centaines de milliers | nombre | journaux des scripts |
| Doublons d'uid de représentants | plusieurs centaines de milliers d'entreprises | entreprises corrigées, doublons supprimés | journaux des scripts |
| Code NAFA 2025 | non chiffré | nombre d'entreprises concernées | journaux des scripts |
 
---
 
## 7. Les questions qu'on te posera
 
**« Comment avez-vous sécurisé une correction sur plusieurs millions de lignes ? »**
Sauvegarde, test sur un échantillon, exécution par lots, contrôles avant et après, possibilité de revenir en arrière. Si tu l'as fait, ajoute-le au CV B : c'est le détail qui distingue un data engineer.
 
**« Et pour que ça ne se reproduise pas ? »**
Ce que tu as remonté ou proposé (causes des uid instables, des désynchronisations). Sinon, ce que tu proposerais : identifiants stables, contrôle au moment de l'envoi de la formalité, contrat de données entre le Guichet unique et le RNE.
 
**« Pourquoi PySpark ici ? »**
Volume et parallélisme. C'est le même raisonnement que la note « DuckDB ou Spark » de ton projet (exercice E4).
 
**« Comment priorisiez-vous les tickets ? »**
Par impact pour l'entreprise concernée (une radiation erronée bloque son activité), par ancienneté et par volume de cas similaires.
 
### Trois histoires STAR à rédiger
 
| Histoire | CV | Situation, en une phrase |
|---|---|---|
| Les uid instables | A et B | Des formalités restées en brouillon échouaient au dépôt, car les identifiants avaient changé entre-temps. |
| L'harmonisation Guichet unique / RNE | B | Des règles de gestion divergentes entre deux systèmes touchaient [N] millions de SIREN. |
| Les désynchronisations inter-sources | A | Des entreprises radiées à tort, faute de synchronisation entre le RNE, les greffes et l'Insee. |
 
Format : situation, ta tâche, trois actions, un résultat chiffré, ce que tu as appris. 90 secondes à l'oral.
 
---
 
## 8. Traduire le jargon interne
 
| Terme interne | Formulation pour un recruteur |
|---|---|
| GLPI | tickets d'incidents qualité |
| MQL | MongoDB |
| formalité | déclaration d'une entreprise (création, modification, cessation) déposée sur le Guichet unique |
| uid | identifiant interne d'un objet (représentant, activité) |
| erreur 500 | échec de traitement côté serveur |
| mise en conformité | correction d'exactitude ou de structure |
| DBeaver | client SQL : dans la ligne d'outils, pas dans les puces |
 
---
 
## 9. Points de vigilance
 
- Ordres de grandeur et nature des tâches : c'est normal sur un CV. Aucun nom, SIREN, capture d'écran ou détail de faille interne.
- Les uid étaient corrigés à la main : ne les présente pas comme une automatisation. L'argument, c'est le diagnostic et le volume traité.
- Relie l'INPI au projet : tu as déjà mené une migration de nomenclature en production (NAFA 2025). C'est ton histoire pour la bascule NAF 2025 de la plateforme, sur les deux CV.