

from bs4 import BeautifulSoup
import urllib
import sys  
import os
from PyQt4.QtGui import *  
from PyQt4.QtCore import *  
from PyQt4.QtWebKit import *  
from lxml import html 
import dryscrape
import pickle
import json
from unidecode import unidecode
import re



class SeasonData2(object):
    """scrape a seasons worth of match and player data from fourfourtwo.com and save as pkld dictionary"""    
    def __init__(self, year):
        self.year = year
        print self.year
        self.season = self.season_links(self.year)
        
        for gameName,game in self.season.iteritems():
            path = '/media/sf_VirtualBox/Football/'
            if not os.path.exists(path + year + "/" + game['homeTeam'] + '_' + game['awayTeam'] + ".pkl"):
                
                print gameName
                game['match_stats'] = self.match_stats(game['link'])
                game['home_players'], game['away_players'] = self.player_links(game['link'])
                
                for playerName, player in game['home_players'].iteritems():
                    print playerName
                    player['player_stats'] = self.player_stats(player['link'])
                for playerName, player in game['away_players'].iteritems():
                    print playerName
                    player['player_stats'] = self.player_stats(player['link'])
                
                output = open(path + year + "/" + game['homeTeam'] + '_' + game['awayTeam'] + ".pkl", 'wb')
                pickle.dump(game, output, protocol=2)
                output.close()
                
                
        
        
    #list of all mathces in list links
    def season_links(self, year):
        resultsPage = urllib.urlopen("http://www.fourfourtwo.com/statszone/results/8-" + year)
        resultsPageSoup = BeautifulSoup(resultsPage, "lxml")
        scores = resultsPageSoup.findAll('td', {'class': 'score'})
        homeTeams = resultsPageSoup.findAll('td', {'class': 'home-team'})
        awayTeams = resultsPageSoup.findAll('td', {'class': 'away-team'})
        #matches = [homeTeams[i].contents[0].strip()+"_"+awayTeams[i].contents[0].strip() for i in range(0,len(homeTeams))]
        gamesStatsLinks = ['http://www.fourfourtwo.com' + 
                           l.a['href'] for l in resultsPageSoup.findAll('td', {'class': 'link-to-match'})]

        season = {}

        for i in range(0,len(homeTeams)):
            season[homeTeams[i].contents[0].replace(" ", "") + "_" + awayTeams[i].contents[0].replace(" ", "")] = {
                "homeTeam":str(homeTeams[i].contents[0]).replace(" ",""),
                "awayTeam":str(awayTeams[i].contents[0]).replace(" ",""),
                "homeGoals":int(scores[i].contents[0].split("-")[0]),
                "awayGoals":int(scores[i].contents[0].split("-")[1]),
                "link":str(gamesStatsLinks[i])
            }

        return(season)
    
    
    
    def match_stats(self, link):
        resultsPage = urllib.urlopen(link)
        resultsPageSoup = BeautifulSoup(resultsPage, "lxml")

        #overall statistics
        match_stats = {}
        possession = resultsPageSoup.findAll('div', {'id':'summary_possessions'})[0].findAll('svg', {'class': 'doughnut_chart'})[0].text
        match_stats['home_possession'] = float(possession.split('%')[0])
        match_stats['away_possession'] = float(possession.split('%')[1])


        match_stats['home_pass_cmplt'] = int(resultsPageSoup.findAll('div', {'id':'summary_passes'})[0].findAll('text', {'fill': "#FCD800"})[0].next)
        match_stats['away_pass_cmplt'] = int(resultsPageSoup.findAll('div', {'id':'summary_passes'})[0].findAll('text', {'fill': "#E6E6E6"})[0].next)

        match_stats['home_crnr'] = int(resultsPageSoup.findAll('div', {'id':'summary_corners'})[0].findAll('text', {'fill': "#FCD800"})[0].next)
        match_stats['away_crnr'] = int(resultsPageSoup.findAll('div', {'id':'summary_corners'})[0].findAll('text', {'fill': "#E6E6E6"})[0].next)

        match_stats['home_attck_pass'] = int(resultsPageSoup.findAll('div', {'id':'summary_attacking'})[0].findAll('text', {'fill': "#FCD800"})[0].next)
        match_stats['away_attck_pass']= int(resultsPageSoup.findAll('div', {'id':'summary_attacking'})[0].findAll('text', {'fill': "#E6E6E6"})[0].next)

        match_stats['home_shots'] = int(resultsPageSoup.findAll('div', {'id':'summary_shots'})[0].findAll('text', {'fill': "#FCD800"})[0].next)
        match_stats['away_shots'] = int(resultsPageSoup.findAll('div', {'id':'summary_shots'})[0].findAll('text', {'fill': "#E6E6E6"})[0].next)

        match_stats['home_fouls'] = int(resultsPageSoup.findAll('div', {'id':'summary_fouls'})[0].findAll('text', {'fill': "#FCD800"})[0].next)
        match_stats['away_fouls'] = int(resultsPageSoup.findAll('div', {'id':'summary_fouls'})[0].findAll('text', {'fill': "#E6E6E6"})[0].next)

        match_stats['date_location'] = resultsPageSoup.findAll('div', {'class': 'teams'})[0].next.strip()

        match_stats['date'] = str(match_stats['date_location'].split(',')[-2])
        match_stats['time'] = str(match_stats['date_location'].split('-')[-1])
        
        home_goals_raw = resultsPageSoup.findAll('div',{'class':'home'})[0].contents
        match_stats['home_goals_times'] = []
        for el in home_goals_raw:
            if str(el) != '\n':
                match_stats['home_goals_times'].append(int(re.sub("[^0-9]", "", str(el.contents))))
                
        away_goals_raw = resultsPageSoup.findAll('div',{'class':'away'})[0].contents
        match_stats['away_goals_times'] = []
        for el in away_goals_raw:
            if str(el) != '\n':
                match_stats['away_goals_times'].append(int(re.sub("[^0-9]", "", str(el.contents))))
                
        return(match_stats)


    def player_links(self, game_link):
        url = game_link + '/player-stats#tabs-wrapper-anchor'
        session = dryscrape.Session()
        session.visit(url)
        formatted_result = session.body()

        soup = BeautifulSoup(formatted_result, 'html5lib')
        home_players = soup.findAll('div', {'class': 'lineup home'})
        away_players = soup.findAll('div', {'class': 'lineup away'})


        home_player_urls = ['http://www.fourfourtwo.com' + player.findAll('a')[0]['href'] 
           for player in home_players]
        home_player_names = [player.findAll('a')[0].contents
           for player in home_players]

        away_player_urls = ['http://www.fourfourtwo.com' + player.findAll('a')[0]['href'] 
           for player in away_players]
        away_player_names = [player.findAll('a')[0].contents
           for player in away_players]

        home_players = {}
        for i in range(len(home_player_names)):
            home_players[str(unidecode(home_player_names[i][0]))] = {"link":str(home_player_urls[i]) }

        away_players = {}
        for i in range(len(away_player_names)):
            away_players[str(unidecode(away_player_names[i][0]))] = {"link":str(away_player_urls[i]) }

        return(home_players, away_players)


    
    def player_stats(self, url):
        #
        
        session = dryscrape.Session()
        session.visit(url)
        playerPageFormatted = session.body()
        playerSoup = BeautifulSoup(playerPageFormatted, 'html5lib')

        match_stats = {}
        #passes
        match_stats['pass_success'] = len(playerSoup.findAll('line', {'marker-end': 'url(#smallblue)'}))
        match_stats['pass_fail'] = len(playerSoup.findAll('line', {'marker-end': 'url(#smallred)'}))
        match_stats['chances'] = len(playerSoup.findAll('line', {'marker-end': 'url(#smalldeepskyblue)'}))
        match_stats['assists'] = len(playerSoup.findAll('line', {'marker-end': 'url(#smallyellow)'}))

        #shots
        match_stats['on_target'] = len(playerSoup.findAll('line', {'marker-end': 'url(#bigblueend)'}))
        match_stats['off_target'] = len(playerSoup.findAll('line', {'marker-end': 'url(#bigredend)'}))
        match_stats['on_target'] = len(playerSoup.findAll('line', {'marker-end': 'url(#bigblueend)'}))
        match_stats['goals'] = len(playerSoup.findAll('line', {'marker-start': 'url(#bigyellowend)'}))

        #takeons
        match_stats['takeon_success'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/success.png'}))
        match_stats['takeon_fail'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/fail.png'}))

        #defensive
        match_stats['fail_tkl'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/failed_tackle.png'}))
        match_stats['success_tkl'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/successful_tackle.png'}))
        match_stats['success_clearence'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/successful_clearence.png'}))
        match_stats['failed_clearence'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/failed_clearence.png'}))
        match_stats['interception'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/interceptions.png'}))
        match_stats['ball_recovery'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/defensive-ball-clearence.png'}))
        match_stats['blocks'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/blocks.png'}))
        match_stats['blocks_cross'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/blocks-cross.png'}))

        #aerial
        match_stats['aerial_won'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/won.png'}))
        match_stats['aerial_lost'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/lost.png'}))

        #fouls
        match_stats['foul_cmt'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/commited.png'}))
        match_stats['foul_sfr'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/suffered.png'}))

        #errors
        match_stats['error_goal'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/error-leading-goal.png'}))
        match_stats['error_shot'] = len(playerSoup.findAll('image', {'href': '/sites/fourfourtwo.com/modules/custom/statzone/files/icons/error-leading-shot.png'}))

        return(match_stats)

    
        




if __name__ == '__main__':
    SeasonData2('2015')

