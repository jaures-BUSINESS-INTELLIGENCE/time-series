

## Stage 0 – Framing

### Reflection 1: How to check that real data exists

I would have searched the web and looked at several data providers and APIs to see
if real historical CO2 data was available. More precisely, I would have read the
documentation of one API to find a parameter for past data (here `past_days`) and
then made one test request to see how many days I really get back.

The plan to use fake data was based on an assumption that nobody had checked. An
assumption about what data exists is itself a claim, and checking it takes a few
minutes. This is the acquisition discipline of CM3.

<!--
FR :
Réflexion 1 : comment vérifier que des données réelles existent

J'aurais fait des recherches sur le web et regardé plusieurs fournisseurs de données
et API pour voir si des données historiques réelles de CO2 existaient. Plus
précisément, j'aurais lu la documentation d'une API pour trouver un paramètre pour
les données passées (ici past_days), puis fait une requête de test pour voir
combien de jours je reçois vraiment.

Le plan avec des données inventées reposait sur une hypothèse que personne n'avait
vérifiée. Une hypothèse sur les données qui existent est elle-même une affirmation,
et la vérifier prend quelques minutes.
-->
## Stage 1 – Collection

### Reflection 2: My prediction before seeing the data

I predict that CO2 in Le Mans went down over the last 90 days (early August to
early November). My reasoning: in August it is summer, and from late October it is
autumn, with a colder and windier weather. I will check this prediction against my
real data in Stage 3.

<!--
FR :
Réflexion 2 : ma prédiction avant de voir les données

Je prédis que le CO2 au Mans a baissé sur les 90 derniers jours (début août à début
novembre). Mon raisonnement : en août c'est l'été, et à partir de fin octobre c'est
l'automne, avec un temps plus froid et plus venteux. Je vérifierai cette prédiction
avec mes vraies données à l'étape 3.
-->
**Follow-up after running the pipeline:** My prediction was wrong. The series went up (+0.1376 ppm/day), not down. I guessed from the seasons, but this is a model estimate with a lot of day-to-day noise, so the season alone did not explain it.
<!-- Suite après exécution : ma prédiction était fausse. La série a monté, pas baissé. J'ai deviné avec les saisons, mais c'est une estimation de modèle avec beaucoup de bruit d'un jour à l'autre. -->
## Stage 2 – Cleaning

### Reflection 3: Is the gap detection unnecessary if my run finds no gaps?

No, I would not delete the gap-detection code. My run found no gaps because
Open-Meteo's air-quality data comes from a model that fills every hour, and my test
request returned 2,160 hourly values with no empty one. But "this source was clean
this time" is only an observation. It is not a guarantee that the source will always
be clean.

My pipeline runs alone every Monday at 6am and nobody watches it. If one day the API
returned a day without values, a missing day would pass unnoticed, and the trend line
would be computed on incomplete data without anyone knowing. This is the same danger
as a silent failure: the problem is invisible. The detection code costs only a few
lines, while the error it prevents can be serious. A real sensor would also drop
readings from time to time, so the code makes the pipeline reusable with other sources.

<!--
FR :
Réflexion 3 : la détection de trous est-elle inutile si mon exécution n'en trouve aucun ?

Non, je ne supprimerais pas le code de détection de trous. Mon exécution n'a trouvé
aucun trou parce que les données de qualité de l'air d'Open-Meteo viennent d'un
modèle qui remplit chaque heure, et ma requête de test a renvoyé 2 160 valeurs
horaires sans aucune valeur vide. Mais « cette source était propre cette fois » n'est
qu'une observation. Ce n'est pas une garantie que la source sera toujours propre.

Mon pipeline tourne seul chaque lundi à 6 h et personne ne le surveille. Si un jour
l'API renvoyait une journée sans valeurs, un jour manquant passerait inaperçu, et la
droite de tendance serait calculée sur des données incomplètes sans que personne ne
le sache. C'est le même danger qu'un échec silencieux : le problème est invisible. Le
code de détection ne coûte que quelques lignes, alors que l'erreur qu'il évite peut
être grave. Un vrai capteur perdrait aussi des mesures de temps en temps, donc ce
code rend le pipeline réutilisable avec d'autres sources.
-->
### Reflection 4 — Rolling mean or exponential smoothing?

Both methods make a noisy series smoother, but they react differently to new data.

The rolling mean (window 7) gives the same weight to the last 7 days and ignores older days. It is stable and easy to explain. I would use it when the data is noisy and I want a calm, simple trend, for example for a weekly report.

Exponential smoothing (alpha 0.3) gives more weight to recent days and less to old ones. It reacts faster to a real change. I would use it when I want to notice a change early, for example an alert system.

My data shows this clearly. On the last days, the CO2 value jumped from 449.6 to 459.5 and then to 470.5. The rolling mean only went from 450.3 to 453.49, because the 5 older days pull it back. The exponential smoothing went from 451.78 to 457.4, so it follows the jump more closely.

The price of reacting faster is that exponential smoothing can also follow a one-day spike that is only noise. So: rolling mean when I want stability, exponential smoothing when I want speed. With a high alpha it is faster but noisier, and with a low alpha it is calmer but slower.

<!-- Réflexion 4 — Moyenne glissante ou lissage exponentiel ?
Les deux méthodes lissent une série bruitée, mais elles réagissent différemment aux nouvelles données.
La moyenne glissante (fenêtre 7) donne le même poids aux 7 derniers jours et ignore les plus anciens. Elle est stable et facile à expliquer. Je l'utiliserais quand les données sont bruitées et que je veux une tendance calme et simple, par exemple pour un rapport hebdomadaire.
Le lissage exponentiel (alpha 0,3) donne plus de poids aux jours récents et moins aux anciens. Il réagit plus vite à un vrai changement. Je l'utiliserais pour repérer tôt un changement, par exemple dans un système d'alerte.
Mes données le montrent bien. Sur les derniers jours, le CO2 est passé de 449,6 à 459,5 puis à 470,5. La moyenne glissante n'est passée que de 450,3 à 453,49, car les 5 jours plus anciens la tirent en arrière. Le lissage exponentiel est passé de 451,78 à 457,4, il suit donc mieux le saut.
Le prix de cette rapidité : le lissage exponentiel peut aussi suivre un pic d'un seul jour qui n'est que du bruit. Donc : moyenne glissante pour la stabilité, lissage exponentiel pour la rapidité. Avec un alpha élevé il est plus rapide mais plus bruité, avec un alpha faible plus calme mais plus lent. -->
