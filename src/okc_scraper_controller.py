from selenium.webdriver import Chrome
from pymongo import MongoClient
from datetime import datetime
from urllib.parse import urlparse
import pandas as pd
import numpy as np
import time, os, requests
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys

class Scraper:
    """
    Class for an OkCupid Scraper

    Attributes: 
        name (str): alias for the account that will be used to access OKC for scraping
        driver (WebDriver): tool used to get and navigate web pages
        mongoclient (pymongo.mongo_client.MongoClient): mongo database client to store data
        email (str): email of the scraper account
        pw (str): password of the scraper account
        version (str): date string of the datetime when current version was completed.
    """

    def __init__(self, name, driverpath=f'{os.getcwd()}/src/chromedriver'):
        """
        Constructor for the Scraper class

        Parameters:
            name (str): alias for the account that will be used to access okc for scraping
            driverpath (str): path to the web driver file
        """
        self.name = name
        self.driver = Chrome(driverpath)
        self.db = MongoClient('localhost', 27017).okc

        #get email and password from file
        user = pd.read_csv('src/okc_account_credentials', index_col=0).loc[name]
        self.email = user.email
        self.pw = user.pw


        #fetch current version
        record = self.db.scrapers.find_one({'_id': name})
        if record != None:
            self.version = record['current_version']
        else:
            self.version = None
    
    def login(self):
        """
        Logs in to the scraper's account

        """
        self.driver.get('https://www.okcupid.com/login')
        time.sleep(2)

        self.driver.find_element_by_class_name('accept-cookies-button')\
            .click()
        time.sleep(1)

        try:
            self.driver.find_element_by_class_name('login-username')\
                .send_keys(self.email)

            self.driver.find_element_by_class_name('login-password')\
                .send_keys(self.pw)

            self.driver.find_element_by_class_name('login-actions-button')\
                .click()

        #sometimes it's a different login form
        except NoSuchElementException:
            self.driver.find_element_by_name('username')\
                .send_keys(self.email)
            self.driver.find_element_by_name('password')\
            .send_keys(self.pw)
            self.driver.find_element_by_class_name('login2017-actions-button')\
                .click()
        time.sleep(2)


    def logout(self):
        """
        Logs the current scraper out.
        """
        self.driver.get('https://www.okcupid.com/logout')


    def set_first_version(self, question_data):
    #TODO docstring
        #qd = self.getScraperQuestionData()
        dt_now = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.db.scrapers.insert_one({    \
             '_id': self.name,           \
             'current_version': dt_now,  \
             'versions':{                \
                dt_now: question_data    \
        }})
        self.version = dt_now

    def getScraperQuestionData(self):
    #TODO docstring
        self.driver.get('https://www.okcupid.com/profile')
        time.sleep(2+np.random.exponential())
        sameq = lambda q1, q2: q1.find_element_by_xpath('button/h3').text ==\
            q2.find_element_by_xpath('button/h3').text
        self.driver.find_element_by_class_name('profile-selfview-questions-more').click()
        time.sleep(2+np.random.exponential())

        questions = self.driver.find_elements_by_class_name('profile-question')
        i = 0
        current = questions[i]
        datalist = []

        while not sameq(current, questions[-1]):
            for j in range(i,len(questions)):
                #open question detail overlay
                questions[j].click()
                #needs a moment to load
                time.sleep(0.3+0.2*np.random.exponential())
                
                #scrape question overlay. 
                overlay = self.driver.find_element_by_class_name('questionspage')

                #get question text
                text = overlay.find_element_by_tag_name('h1').text
                
                #get the choices and what our answer was
                our_answer_buttons = overlay.find_element_by_class_name('pickonebutton-buttons')\
                    .find_elements_by_class_name('pickonebutton-button')
                choices = [b.text for b in our_answer_buttons]
                our_answer = list(map(lambda x: x.get_attribute('class')\
                    .endswith('--selected'),our_answer_buttons)).index(True)

                #get which of their answers we will accept
                their_answer_buttons = overlay.find_element_by_class_name('pickmanybuttons')\
                    .find_elements_by_tag_name('input')
                acceptable = list(map(lambda x: x.get_property('checked'), their_answer_buttons))
                
                #get how important the question is to our scraper
                #should all be 1:somewhat important
                importance_buttons = overlay.find_element_by_class_name('importance-pickonebutton')\
                    .find_elements_by_tag_name('button')
                importance = list(map(lambda b: b.get_attribute('class').endswith('--selected'),\
                    importance_buttons)).index(True)

                #package up the question data
                datalist.append({             \
                    'q_text': text,           \
                    'choices': choices,       \
                    'our_answer': our_answer, \
                    'acceptable': acceptable, \
                    'importance': importance  \
                })

                #exit overlay
                self.driver.find_element_by_class_name('reactmodal-header-close').click()
                
            #adjust loop conditions
            current = questions[j]
            current.location_once_scrolled_into_view
            questions = self.driver.find_elements_by_class_name('profile-question')
            for i in range(len(questions)):
                if sameq(current, questions[i]):
                    break 

        return datalist


    def add_questions_update_version(self, new_question_data):
    #TODO docstring
        dt_now = datetime.now().strftime('%Y%m%d_%H%M%S')

        versions = self.db.scrapers.find_one({'_id':self.name})['versions']
        prev_version = versions[self.version]
        versions[dt_now] = _merge_question_data_versions(prev_version, new_question_data)
        self.db.scrapers.update({'_id':self.name}, {'$set':
            {'versions': versions, 'current_version': dt_now}})
        self.version = dt_now

    #TODO skeleton method - complete
    def _merge_question_data_versions(prev_qd, new_qd):
        '''
        Returns a complete question data list composed of the union of the
        two lists, except old versions of the same questions are replaced with new
        versions.
        '''
        return new_qd

    def _is_same_question(q1, q2):
    #TODO docstring
        '''
        Compares two questions by the question text. Used in _merge----
        '''
        #TODO currently a skeleton method - complete
        return False
        
    def collect_usernames(self, softlimit=np.inf):
    #TODO docstring
        self.driver.get('https://www.okcupid.com/match')
        time.sleep(2)
        usernames = set()
        while len(usernames) < softlimit:
            try:
                self.driver.find_element_by_class_name('blank-state-wrapper')
                return usernames

            except NoSuchElementException:
                try:
                    matchcards = self.driver.find_elements_by_class_name('usercard-thumb')
                    last = matchcards[-1]
                    usernames = usernames.union(set(map(\
                        lambda card: card.get_attribute('data-username'), matchcards)))
                    last.location_once_scrolled_into_view
                except StaleElementReferenceException:
                    time.sleep(0.5+np.random.exponential())
        return usernames

        
    def scrape_user(self, img_save_dir, username, wait=1.5):
        #TODO docstring        
        #TODO need try-accept block for when user isn't found

        #scrape questions first
        self.driver.get(f'https://www.okcupid.com/profile/{username}/questions')
        time.sleep(wait)

        #if there are any unanswered questions, answer them so we can scrape
        #ALL the user's answered questions later.
        if self.get_num_questions_by_filter('FIND OUT') > 0:
            qdata = self.answer_unanswered_questions()
            self.add_questions_update_version(qdata)

        #scrape the questions the user has answered
        questions = self.scrape_user_questions(username)

        #scrape their main profile contents
        self.driver.get(f'https://www.okcupid.com/profile/{username}')
        time.sleep(wait*np.random.exponential())
        try:
            self.driver.find_element_by_class_name('profile-essays-expander').click()
        except NoSuchElementException: #short profiles
            pass
        html = self.driver.find_element_by_tag_name('HTML').get_attribute('innerHTML')
        
        #scrape images
        img_count = self.save_images(img_save_dir, username)
        
        dtime = datetime.now().strftime('%Y%m%d_%H%M%S'),
        
        #package it all up
        return{                                 \
            '_id': username,                    \
            'html': html,                       \
            'img_count': img_count,             \
            'questions': questions,             \
            'metadata':{                        \
                'time': dtime,                  \
                'scraper': self.name,           \
                'scraper_version': self.version \
            }                                   \
        }


    def answer_question_overlay(self, importance_answer=1):
    #TODO docstring
        overlay = self.driver.find_element_by_class_name('questionspage')

        #get button arrays
        our_answer_buttons = overlay.find_element_by_class_name('pickonebutton-buttons')\
            .find_elements_by_class_name('pickonebutton-button')
        their_answer_buttons = overlay.find_element_by_class_name('pickmanybuttons')\
            .find_elements_by_tag_name('input')
        importance_buttons = overlay.find_element_by_class_name('importance-pickonebutton')\
            .find_elements_by_tag_name('button')

        #get data to store
        text = overlay.find_element_by_tag_name('h1').text
        choices = [b.text for b in our_answer_buttons]
        answer = int(np.random.uniform() * len(choices))
        acceptable_arr = [False]*len(choices)
        acceptable_arr[answer] = True

        #click the appropriate buttons
        our_answer_buttons[answer].click()
        their_answer_buttons[answer].click()
        importance_buttons[importance_answer].click()
        
        #submit form
        self.driver.find_element_by_class_name('questionspage-buttons-button--answer')\
            .click()

        return{                           \
            'q_text': text,               \
            'choices': choices,           \
            'our_answer': answer,         \
            'acceptable': acceptable_arr, \
            'importance': importance      \
        }


        
    def answer_unanswered_questions(self, wait=1, importance_answer=1):
    #TODO docstring
        qdata = []
        while self.get_num_questions_by_filter('FIND OUT') > 0:
            try:
                self.driver.find_element_by_class_name('profile-questions-filter-icon--findOut')\
                    .click()
                time.sleep(wait)
                
                self.driver.find_element_by_class_name('profile-question')\
                    .click()
                time.sleep(wait)
                
                qdata.append(self.answer_question_overlay(importance_answer))
                time.sleep(wait)

            except NoSuchElementException:
                wait += 0.1
                time.sleep(wait)
                continue

        return qdata
                
                
    def get_num_questions_by_filter(self, filterstr):
    #TODO docstring
        arr = self.driver.find_element_by_class_name('profile-questions-filters')\
            .text.split('\n')
        return int(arr[arr.index(filterstr)+1])


    def scroll_to_bottom(self, wait):
    #TODO docstring
        body = self.driver.find_element_by_tag_name('body')
        y = [0,1]
        while y[0] != y[1]:
            y[0] = y[1]
            body.send_keys(Keys.END)
            time.sleep(wait)
            y[1] = self.driver.execute_script('return window.pageYOffset;')
            
            
    def scrape_user_questions(self, username):
    #TODO docstring
        q=dict()
        for filterstr in ['AGREE', 'DISAGREE']:
            time.sleep(1)
            q[filterstr] = self.scrape_user_questions_by_filter(filterstr)
        return q


    def scrape_user_questions_by_filter(self, filterstr, wait=0.3):
    #TODO docstring
        self.driver.find_element_by_tag_name('body')\
            .send_keys(Keys.HOME)
        time.sleep(0.7+wait)
        self.driver.find_element_by_class_name(f'profile-questions-filter-icon--{filterstr.lower()}')\
            .click()
        time.sleep(0.7+wait)
        numQsToScrape = self.get_num_questions_by_filter(filterstr) 

        self.scroll_to_bottom(wait)

        questions = self.driver.find_elements_by_class_name('profile-question')
        while len(questions) != numQsToScrape:
            wait += 0.1
            self.scroll_to_bottom(wait)
            questions = self.driver.find_elements_by_class_name('profile-question')
        return [q.get_attribute('innerHTML') for q in questions]


    def get_src(img):
    #TODO docstring
        src = img.get_attribute('src')
        if src is None:
            src = img.get_attribute('data-src')
        return src


    def save_images(self, save_dir, username):
    #TODO docstring
        if not os.path.exists(save_dir):
            os.mkdir(img_save_dir)
        images = self.driver.find_element_by_class_name('profile-thumb')\
            .find_elements_by_tag_name('img')
        images.extend(self.driver.find_element_by_class_name('profile-essays')\
            .find_elements_by_tag_name('img'))

        for url in map(Scraper.get_src,images):
            i = requests.get(url).content
            name = urlparse(url).path.split('/')[-1]
            with open(f'{save_dir}/{username}_{name}', 'wb') as f:
                f.write(i)
        return len(images)


    def answerAllQuestions(self, importance_answer=1):
    #TODO docstring
        self.driver.get('https://www.okcupid.com/profile')
        time.sleep(2+np.random.exponential())
        self.driver.find_element_by_class_name('profile-selfview-questions-more')\
            .click()
        time.sleep(2+np.random.exponential())

        self.driver.find_element_by_class_name('profile-questions-next-actions-button--answer')\
            .click()
        time.sleep(1)

        qdata=[]

        while True:
            try:
                time.sleep(0.75)
                your_answer_buttons = self.driver.find_element_by_class_name('pickonebutton-buttons')\
                    .find_elements_by_tag_name('button')
                acceptable_answers = self.driver.find_element_by_class_name('pickmanybuttons-buttons')\
                    .find_elements_by_tag_name('button')
                importance_buttons = self.driver.find_element_by_class_name(\
                        'importance-pickonebutton-buttons')\
                    .find_elements_by_tag_name('button')
                answer = int(np.random.uniform()*len(your_answer_buttons))
                your_answer_buttons[answer].click()
                acceptable_answers[answer].click()
                importance_buttons[importance_answer].click()
                time.sleep(0.5)

                qdata.append(self.driver.find_element_by_class_name('questionspage')\
                    .get_attribute('innerHTML'))

                driver.find_element_by_class_name('questionspage-buttons-button--answer')\
                    .click()
            except ElementClickInterceptedException:
                continue
        return qdata


    def answer_initial_question(scraper, wait=1):
    #TODO docstring
        qtext = scraper.driver.find_element_by_class_name('convoanswers-text')\
            .text
        choicebuttons = scraper.driver\
            .find_element_by_class_name('convoanswers-answers')\
            .find_elements_by_tag_name('button')
        choicestext = [b.text for b in choicebuttons]
        answer = int(np.random.uniform() * len(choicestext))
        choicebuttons[answer].click()
        time.sleep(wait)

        choicebuttons = scraper.driver\
            .find_element_by_class_name('convoanswers--theirs')\
            .find_elements_by_tag_name('button')
        choicebuttons[answer].click()
        time.sleep(wait)

        scraper.driver.find_element_by_class_name('convoquestion-continue')\
            .click()
        return {                    \
            'q_text': qtext,        \
            'choices': choicestext, \
            'our_answer': answer,   \
            'acceptable': answer,   \
            'importance': 1         \
        }
        #TODO verify the assumed importance answer is right


    def answer_all_initial_questions(scraper, wait=1):
    #TODO docstring
        qdata = []
        current_q, num_qs = get_progress(scraper)
        for i in range(num_qs - current_q+1):
            qdata.append(answer_initial_question(scraper, wait))
            time.sleep(wait*2)
        return qdata


    def get_progress(scraper):
    #TODO docstring
        return tuple(map(int, scraper.driver\
            .find_element_by_class_name('obqconvo-progress-text')\
            .text.split(' of ')))
    
    def save_usernames_to_mongo(self, usernames):
        self.db.usernames.insert_many(map(lambda u: {'_id':u}, usernames))


if __name__ == "__main__":
    ren = Scraper('ren')
    ren.login()
    
    
    usernames = ren.collect_usernames(softlimit=20)
    #[u['_id'] for u in ren.db.usernames.find({'_id':{'$exists':'true'}}, {'_id':'true'})]

    for username in usernames:
        udata = ren.scrape_user('live_images', username)
        ren.db.users.insert_one(udata)













