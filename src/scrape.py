from okc_scraper_controller import Scraper
import pandas as pd

if __name__=='__main__':
    scrapername = pd.read_csv('src/okc_account_credentials', index_col=0).iloc[0].name

    scraper = Scraper(scrapername)
    scraper.login()
    print('login successful')
    
    qd = scraper.get_scraper_question_data()
    print('retrieved inital question data')
    
    #scraper.set_first_version(qd)
    #print('set first version')
    scraper.add_questions_update_version(qd)
    print('version added')

    qd, exit_stat = scraper.answer_all_questions()
    print(exit_stat)
    
    scraper.add_questions_update_version(qd)
    print('version updated')

    scraper.logout()
    print('logged out')
