

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
### Reflection 5 — What if the API fails on every retry?

If the Open-Meteo API fails on all 4 attempts, `fetch_series.py` raises a `RuntimeError`. This makes the first step of the Action fail, so the job stops and turns red.

Because the workflow has no `if: always()` and no `continue-on-error`, the next steps do not run. `analyze_series.py` does not run, and the "Commit updated data" step does not run either. So nothing is committed.

As a result, `data/series.csv` and `docs/data/series_analysis.json` keep the values from the last successful run. They are not deleted and not half-written. The dashboard keeps showing the old data, and `generated_at` keeps the old date. The data is stale, but it is not wrong.

I think this is the right behaviour. A visible failure warns me that something is wrong, and old but correct data is better than an empty or broken file. The weakness is that nobody is told: I only see the red run if I look at the Actions tab. A possible improvement would be to show the age of the data on the dashboard (for example, "last updated 9 days ago").

<!-- Réflexion 5 — Et si l'API échoue à chaque essai ?
Si l'API Open-Meteo échoue aux 4 tentatives, `fetch_series.py` lève une `RuntimeError`. La première étape de l'Action échoue donc, le job s'arrête et devient rouge.
Comme le workflow n'a ni `if: always()` ni `continue-on-error`, les étapes suivantes ne s'exécutent pas. `analyze_series.py` ne tourne pas, et l'étape « Commit updated data » non plus. Rien n'est donc enregistré.
Résultat : `data/series.csv` et `docs/data/series_analysis.json` gardent les valeurs de la dernière exécution réussie. Ils ne sont ni supprimés ni à moitié écrits. Le dashboard continue d'afficher les anciennes données, et `generated_at` garde l'ancienne date. Les données sont périmées, mais pas fausses.
Je pense que c'est le bon comportement. Un échec visible me prévient qu'il y a un problème, et des données anciennes mais correctes valent mieux qu'un fichier vide ou cassé. La faiblesse : personne n'est prévenu, je ne vois le run rouge que si je regarde l'onglet Actions. Une amélioration possible serait d'afficher l'âge des données sur le dashboard (par exemple « mis à jour il y a 9 jours »). -->
### Reflection 6 — How many days would I trust the projection?

I would trust the projection for about 1 to 3 days at most, and only as a rough direction, not as an exact number.

The first reason is noise. The daily values are about 6 ppm away from the trend line on average, and sometimes more than 20 ppm. But the projection only goes up by 0.8 ppm in 7 days (from 448.4 to 449.2). This small change is much smaller than the noise of one day, so the numbers cannot be trusted.

The second reason is that the line is fragile. It starts at 448.4, but the last real value is 470.5. If I remove the last 2 days, the projection drops to about 446.8. So two days are enough to change the result.

The third reason is the data itself: it comes from a model (CAMS) and not from a sensor, the window is only 90 days, and CO2 has a seasonal cycle that a straight line cannot see. I would trust the projection more with a longer history and a model that includes seasons.

<!-- Réflexion 6 — Combien de jours ferais-je confiance à la projection ?
Je ferais confiance à la projection pendant 1 à 3 jours au maximum, et seulement comme une direction approximative, pas comme un chiffre exact.
La première raison est le bruit. Les valeurs journalières s'écartent en moyenne d'environ 6 ppm de la droite de tendance, et parfois de plus de 20 ppm. Or la projection ne monte que de 0,8 ppm en 7 jours (de 448,4 à 449,2). Ce petit changement est bien plus petit que le bruit d'une seule journée, donc les chiffres ne sont pas fiables.
La deuxième raison est que la droite est fragile. Elle démarre à 448,4, mais la dernière valeur réelle est 470,5. Si je retire les 2 derniers jours, la projection tombe à environ 446,8. Deux jours suffisent donc à changer le résultat.
La troisième raison concerne les données : elles viennent d'un modèle (CAMS) et non d'un capteur, la fenêtre n'est que de 90 jours, et le CO2 a un cycle saisonnier qu'une droite ne voit pas. Je ferais plus confiance à la projection avec un historique plus long et un modèle qui inclut les saisons. -->
### Reflection 7 — Why did the pipeline keep working after I changed the location?

I changed only one line in `fetch_series.py`: the coordinates (`LAT, LON`), from Le Mans to Yaoundé. I did not change anything in `analyze_series.py`, and the pipeline still worked. The dashboard showed new values (trend +0.0593 ppm/day instead of +0.1376, last value 448.1 ppm instead of 470.5).

There are three reasons. First, the functions do not know what the data is. `aggregate_to_daily`, the cleaning step, the rolling mean, the exponential smoothing and the projection only work with lists of dates and numbers. They never mention CO2, a city, or a unit. Second, only the input changed, not the logic. The same steps ran on a different series. Third, the dashboard reads a JSON file with a fixed format (`raw`, `rolling_mean`, `exp_smoothed`, `projection`). As long as this format stays the same, the page works, and the chart even adapted its y-axis by itself.

But the pipeline is not fully generic. The honesty note is written in the analysis script and talks about the Northern Hemisphere and summer/autumn, which fits Le Mans better than Yaoundé, a city close to the equator. Some texts on the page also had the city name written by hand ("Le Mans"), and I had to change them. If I changed the variable to pm2_5, the unit and the texts about CO2 would need to change too.

So a good pipeline separates the data, the logic and the presentation, and it keeps the texts that depend on the data (place, unit, seasons) out of the code, or generates them from the data.

<!-- Réflexion 7 — Pourquoi le pipeline a-t-il continué à fonctionner après le changement de lieu ?
J'ai changé une seule ligne dans `fetch_series.py` : les coordonnées (`LAT, LON`), du Mans à Yaoundé. Je n'ai rien changé dans `analyze_series.py`, et le pipeline a continué à fonctionner. Le dashboard a affiché de nouvelles valeurs (tendance +0,0593 ppm/jour au lieu de +0,1376, dernière valeur 448,1 ppm au lieu de 470,5).
Il y a trois raisons. D'abord, les fonctions ne savent pas ce que sont les données. `aggregate_to_daily`, le nettoyage, la moyenne glissante, le lissage exponentiel et la projection travaillent seulement sur des listes de dates et de nombres. Elles ne mentionnent jamais le CO2, une ville ou une unité. Ensuite, seule l'entrée a changé, pas la logique : les mêmes étapes ont tourné sur une autre série. Enfin, le dashboard lit un fichier JSON au format fixe (`raw`, `rolling_mean`, `exp_smoothed`, `projection`). Tant que ce format reste le même, la page fonctionne, et le graphique a même adapté son axe y tout seul.
Mais le pipeline n'est pas entièrement générique. La note d'honnêteté est écrite dans le script d'analyse et parle de l'hémisphère nord et de l'été/automne, ce qui convient mieux au Mans qu'à Yaoundé, ville proche de l'équateur. Certains textes de la page avaient aussi le nom de la ville écrit à la main (« Le Mans ») et j'ai dû les changer. Si je changeais la variable pour pm2_5, l'unité et les textes sur le CO2 devraient aussi changer.
Un bon pipeline sépare donc les données, la logique et la présentation, et garde les textes qui dépendent des données (lieu, unité, saisons) hors du code, ou les génère à partir des données. -->
