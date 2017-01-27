
# coding: utf-8

# In[5]:

from bs4 import BeautifulSoup
import urllib
import sys  
import os
from PyQt4.QtGui import *  
from PyQt4.QtCore import *  
from PyQt4.QtWebKit import *  
from lxml import html 


# In[6]:

#class for rendering js pages for use with BS
class Render(QWebPage):  
    def __init__(self, url):  
        self.app = QApplication(sys.argv)  
        QWebPage.__init__(self)  
        self.loadFinished.connect(self._loadFinished)  
        self.mainFrame().load(QUrl(url))  
        self.app.exec_()  
  
    def _loadFinished(self, result):  
        self.frame = self.mainFrame()  
        self.app.quit() 


# In[7]:

class SeasonData(object):
    
    def __init__(self, year):
        self.year = year
        print self.year
        self.season = self.season_links(self.year)
        
        for gameName,game in self.season.iteritems():
            
            if not os.path.exists(year + "/" + game['homeTeam'] + '_' + game['awayTeam'] + ".pkl"):
                
                print gameName
                game['match_stats'] = self.match_stats(game['link'])
                game['players'] = self.player_links(game['link'])
                
                for playerName, player in game['players'].iteritems():
                    print playerName
                    player['player_stats'] = self.player_stats(player['link'])
                
                output = open(year + "/" + game['homeTeam'] + '_' + game['awayTeam'] + ".pkl", 'wb')
                pickle.dump(mydict, game)
                output.close()
                
                
        
        
    #list of all mathces in list links
    def season_links(self, year):
        resultsPage = urllib.urlopen("http://www.fourfourtwo.com/statszone/results/8-" + year)
        resultsPageSoup = BeautifulSoup(resultsPage)
        scores = resultsPageSoup.findAll('td', {'class': 'score'})
        homeTeams = resultsPageSoup.findAll('td', {'class': 'home-team'})
        awayTeams = resultsPageSoup.findAll('td', {'class': 'away-team'})
        #matches = [homeTeams[i].contents[0].strip()+"_"+awayTeams[i].contents[0].strip() for i in range(0,len(homeTeams))]
        gamesStatsLinks = ['http://www.fourfourtwo.com' + 
                           l.a['href'] for l in resultsPageSoup.findAll('td', {'class': 'link-to-match'})]

        season = {}

        for i in range(0,len(homeTeams)):
            season[homeTeams[i].contents[0].replace(" ", "") + "_" + awayTeams[i].contents[0].replace(" ", "")] = {
                "homeTeam":homeTeams[i].contents[0],
                "awayTeam":awayTeams[i].contents[0],
                "homeGoals":int(scores[i].contents[0].split("-")[0]),
                "awayGoals":int(scores[i].contents[0].split("-")[1]),
                "link":gamesStatsLinks[i]
            }

        return(season)
    
    
    
    def match_stats(self, link):
        resultsPage = urllib.urlopen(link)
        resultsPageSoup = BeautifulSoup(resultsPage)

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

        match_stats['date'] = match_stats['date_location'].split(',')[-2]
        match_stats['time'] = match_stats['date_location'].split('-')[-1]
        return(match_stats)


    def player_links(self, game_link):
        url = game_link + '/player-stats#tabs-wrapper-anchor'
        r = Render(url)
        result = r.frame.toHtml()
        formatted_result = str(result.toAscii())
        soup = BeautifulSoup(formatted_result, 'html5')
        player_urls = ['http://www.fourfourtwo.com' + a['href'] 
                   for a in soup.findAll('div', {'id':'lineups'})[0].findAll('a')]
        player_names = [a.contents
                   for a in soup.findAll('div', {'id':'lineups'})[0].findAll('a')]

        players = {}
        for i in range(len(player_names)):
            players[player_names[i][0]] = {"link":player_urls[i] }

        return(players)

    
    def player_stats(self, url):
        #
        playerPage = Render(url)
        playerPageRendered = playerPage.frame.toHtml()
        playerPageFormatted = str(playerPageRendered.toAscii())
        playerSoup = BeautifulSoup(playerPageFormatted, 'html5')

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

    
        


SeasonData('2015')





