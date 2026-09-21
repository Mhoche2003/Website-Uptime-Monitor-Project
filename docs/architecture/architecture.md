# Architecture

![Architecture](architecture.png)

Le schema montre les deux pipelines qui composent le systeme.

## Pipeline de monitoring

Une regle EventBridge declenche les 3 Lambdas de check (availability, latency, content) toutes les 5 minutes. Chacune envoie une requete HTTPS vers le site surveille, enregistre le resultat dans la table DynamoDB `check history`, et publie une alerte sur le topic SNS en cas d'echec. SNS envoie ensuite un email au proprietaire du site.

## Pipeline du dashboard

Une seconde regle EventBridge, independante de la premiere, declenche la Lambda `aggregate metrics`. Elle lit l'historique dans DynamoDB, calcule les metriques du mois en cours et ecrit le resultat dans un fichier `metrics.json` sur le bucket S3 du dashboard. Le dashboard est consulté séparemment par le site owner. 
## Pourquoi deux pipelines separes

Les checks et l'agregation des metriques n'ont pas besoin de tourner a la meme frequence: les checks doivent etre reactifs (toutes les 5 minutes) pour detecter une panne rapidement, alors que le dashboard n'a pas besoin d'etre mis a jour aussi souvent Donc en séparant les deux, ça evite de recalculer les metriques a chaque check.
