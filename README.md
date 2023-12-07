# NBA Season Predictor

I wanted to build a model that could reasonably predict an NBA team's record and playoff qualification for the upcoming season based on the results from the previous season. This seemed like a decently doable task and since I had already built a web scraper for NBA players it wouldn't take much work to build one for NBA teams.

## Oh, how wrong I was
Ok, so it turns out that it's as tough to scrape NBA team data, or at least data that you want to work with. First things first, the way the NBA looks right now is relatively fresh. Several teams in the 2000s saw shifts in location whether it be due to seeking new markets like the Vancouver Grizzlies and Seattle SuperSonics or because of disaster like the New Orleans Hornets. The NBA hasn't changed since 2014, but those changes of earlier years makes it tough to keep track of the different URLs for each team. This issue comes up when getting to the final data where we look at a team's previous season since I have to manually code in that the Oklahoma City Thunder's first season should be predicted by the Seattle SuperSonics last season. And it's impossible for others teams like the Charlotte Bobcats that had a gap in franchise existence making their first season unpredictable.

## The data
The team gathers every possible normal and advanced stat from a team's previous season such as Win Percentage, Offensive Rating, Margin of Victory, etc as well as previous season success like record and how far they went into the playoffs. However, it gets tricky in some advanced stats like VORP, WS, and BPM since I initially summed the VORP, WS, BPM of the whole roster. This proved to be problematic as the advanced stats, while useful, can be drastically inflated without a big enough sample size of player playing time. For example, the 2022-2023 Denver Nuggets team won the championship but their team BPM (box plus/minus) totals to a whopping -27.9 meaning that per 100 possessions the team is -27.9 points worse than the average team (I'm taking some liberties with the definition since it is supposed to be a player stat). Of course this poses some issues as this doesn't line up with them being a championship caliber team and almost surely making another deep run this upcoming season. Further investigation shows that this large negative number is created by players like Thomas Bryant who had only played 18 games (22% of an NBA season) and only 205 minutes (11 minutes a game) which, relatively speaking is a small sample size. So, I decided to not count players that had not played at least 30 games and 410 minutes. This now puts this Nuggets team at +1.2 BPM. It's still not indicative of great success but it's much better than before.

The second big thing I wanted to add separate of the given data was offseason changes. This was important to capture for cases like the 2010-2011 Miami Heat adding future Hall of Famers LeBron James and Chris Bosh to the team and becoming title favorites (they lost in the Finals, but... still wow). I calculated offseason transactions by looking at the added players' and the outgoing players' advanced stats and taking their difference. This was huge for teams like the 2010-2011 Miami Heat as their Added VORP, Added WS, and Added BPM were +11.7, +27.6, +9.8, respectively. 

Staff changes can be tremendous boosts to a team or complete negatives as well as indications of intentions to compete or tank. These were simply boolean indications of whether the head coach to start the season was different the coach to end the team's previous season. The logic here is that there would be consistency and thus insignificant change if the interim coach, replacing the head coach fired midseason, became the head coach for the following season. 

The draft can prove to be valuable in a teams future success like the Bulls drafting Michael Jordan and the Cavs drafting LeBron James. However, I can't project a player's success based on their college or international stats (as of right now) so I simple listed a team's highest draft pick as a hopeful indicator of higher draft picks meaning likelier success.

Lastly, I added the salary total to the data set. This is another potentially positive indicator of success since a higher payroll suggests that a team is paying more high quality players with the intention of competing for a championship as opposed to teams that don't spend as heavily. Of course this isn't perfect since younger players tend to get paid less than their veteran counterparts even if they are of equal stature. For example, the Oklahoma City Thunder and the Sacramento Kings have the 21st and 23rd ranked payroll, respectively, but are teams that I believe will make the playoffs, while the Chicago Bulls have the 10th highest payroll and have started this season poorly.

## Using the data
There is a looming issue with sticking all this information into one big dataset - the NBA standards change every year. The best example for this is salary. The salary cap in 2001 (where our data starts) was $42.5 million dollars. That has ballooned to $136 million dollars for this season. The same problem appears with defensive and offensive stats. Offense has taken off with games where both teams end with less than 100 points have become a rarity and games with both teams scoring over 120 points a regular occurence. Additionally, the offseason trade of Kawhi Leonard to the Toronto Raptors may not be as good as the Miami offseason acquisitions of LeBron and Bosh but it was easily best addition during the 2018 offseason and needs to be appropriately compared to others in its season.

So, comparing the data directly between seasons doesn't make sense since we would lots of skews in the data. We can solve this issue by keeping the scope within individual seasons. We standard normalize each season's stats that way the top spenders, top offenses, and top acqusitions of a decade ago aren't skewed but actually comparable to those of this past season. We leave the boolean stats and win percentages untouched since have consistent measurements (except for the lockout and COVID seasons).

## Results
The 2002-2022 data was divided into training and validation datasets with 80%/20% splits and tested on the 2023-2024 season data. The average win difference between the prediction and reality hover around 7.5 games going as low as the high 6's. The playoff correctness hovers around 75% as well going as high as 80% depending on the data split. Below I have two results from the RandomForestRegression implementation since the Neural Network implementation took much longer and gave either similar or worse results. The Western Conference is kept on the left and Eastern Conference on the right where each are sorted by their win percentage.

<img tite="Result 1" src="https://github.com/gio-puter/NBA-Season-Predictor/blob/main/Season%20Predictor%20Results%201.png?raw=true" width="650" hspace="20" align="center"/> 
<img title="Result 2" src="https://github.com/gio-puter/NBA-Season-Predictor/blob/main/Season%20Predictor%20Results%202.png?raw=true" width="650" hspace="20" align="center"/>

We can notice that the rankings are generally the same even though the win percentages may waver. We also find some oddities where the Sacramento Kings are predicted to be the 3rd best team in the West but have a smaller playoff likelihood than teams below them. The other thing to recognize is that the RandomForestRegressor model isn't as bold as a neural network would be. The San Antonio Spurs are predicted to get around 30 wins and the Denver Nuggets are predicted to get around 50 wins. This lack of boldness holds the model back where a human would probably say the Spurs are going to reach 15-20 wins and the Nuggets will end with 56-60 wins. Another takeaway from the results shown here as well as from looking at the validation results is that if the prediction results are ≥70% then the team is pretty much a lock to make the playoffs and if they are ≤30% then they are sure to miss the playoffs. This looks good as San Antonio, Portland, Utah, Washington, and Detroit are pretty much out of the playoff race at this point in the NBA season. On the flip side, things generally line up pretty well with playoff contention but there are some outliers that pose some issues within the model's construction.

## Things that the data misses
The starkest difference between the current NBA standings and this prediction is Memphis' placement. Currently, Memphis ranks near the bottom of the league whereas here they finish top 2. This mostly lends to the fact that Memphis is without their best player in Ja Morant for the first 25 games as he has been suspended and key role players being injured. The data does not take into account existing injuries or suspensions leading into the season.

There are other big jumps comparing reality to prediction such as with the Orlando Magic, Minnesota Timberwolves, and Golden State Warriors.
