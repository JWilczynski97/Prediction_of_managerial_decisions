# Copyright (c) Jakub Wilczyński 2020
from time import asctime, localtime, sleep
from os import mkdirs, path, getcwd
from random import uniform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from selenium.common.exceptions import NoSuchElementException

###### WEB DRIVER OPTIONS #####
options = Options()
options.add_argument('start-maximized')  # maximize of the browser window
options.add_experimental_option("excludeSwitches",
                                ['enable-automation'])  # process without information about the automatic test
options.add_argument("chrome.switches")
options.add_argument("--disable-extensions")
browser = webdriver.Chrome(executable_path='C:\Chromedriver\chromedriver.exe', options=options)

##### important structures #####
ALL_SEASONS = ['2010/2011', '2011/2012', '2012/2013', '2013/2014', '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019', '2019/2020']
number_of_downloaded_matches = 0  # it helps to number the downloaded files

########## functions ##########
def create_directory_for_files(folder):
    """This function creates directory (if doesn't exist) for the files included downloaded websites.

    :param folder: str, name of folder coming from current season name"""
    if not path.exists(getcwd() + folder):
        mkdirs(getcwd() + folder)

def cookies_accept():
    """Clicking the 'cookies accept' buttons"""
    more_options_cookies_button = browser.find_element_by_xpath('//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]')
    more_options_cookies_button.click()
    sleep(uniform(3, 5))  # time sleep generator

def is_element_clickable(element):
    """If the element isn't clickable, the current page waits next 3-4 seconds.

    :param element: Element, the element from the current page"""
    if not element_to_be_clickable(element):
        print("The element is not yet clickable. Waiting...")
        sleep(uniform(8, 10))
    if not element_to_be_clickable(element):
        raise Exception("Unexpected error! The element is not clickable. Script ends: {}".format(asctime(localtime())))

def select_season(selected_season):
    """This function selects the correct season from "ALL_SEASONS" in the drop down menu on the start page.

    :param selected_season: str, name of options in drop down menu 'season' """
    drop_down_menu = browser.find_element_by_name("seasons")
    is_element_clickable(drop_down_menu)
    all_options = drop_down_menu.find_elements_by_tag_name("option")
    is_element_clickable(all_options)

    for option in all_options:
        if option.get_attribute("text") == selected_season:
            drop_down_menu.click()
            sleep(uniform(1.5, 2.5))
            option.click()
            sleep(uniform(1.5, 2.5))
            break

def select_stage(stage):
    """This function selects and runs the website with games of the interesting stage."""
    menu = browser.find_element_by_name("stages")
    all_options = menu.find_elements_by_tag_name("option")
    is_element_clickable(menu)
    is_element_clickable(all_options)
    for option in all_options:
        if str(option.get_attribute("text")) == stage or str(option.get_attribute("text")) == "UEFA " + stage:
            menu.click()
            sleep(uniform(1.5, 2.5))
            option.click()
            sleep(uniform(1.5, 2.5))
            break

    # the all matches of stage are located in the Fixtures subpage
    fixtures_button = browser.find_element_by_link_text("Fixtures")
    is_element_clickable(fixtures_button)
    fixtures_button.click()
    sleep(uniform(3, 4))

def download_match():
    """The match downloading function starts in "Match Center" section of the match website, then comes to the Preview."""
    is_preview = False
    sleep(uniform(25, 30))
    html_code = browser.page_source
    save_file(is_preview, html_code)  # saving the website with line-up
    preview_button = browser.find_element_by_link_text("Preview")
    is_element_clickable(preview_button)
    preview_button.click()
    is_preview = True
    sleep(uniform(10, 12))
    html_code_preview = browser.page_source
    save_file(is_preview, html_code_preview)  # saving the website with preview
    print(browser.title[:-19])
    sleep(uniform(4, 5))

def download_websites():
    """The match websites downloading from Group or Final Stage website."""
    matches = browser.find_elements_by_xpath('//*[@id="tournament-fixture"]/div/div/div[8]/a')
    links = []
    print('Matches: ' + str(len(matches)))
    for match in matches:  # it saves the links from href parameters of website elements into the list
        link = match.get_attribute("href")
        links.append(link)
    sleep(uniform(1.5, 2.5))
    for link in links:  # it opens every link to the match website and downloads html code
        browser.execute_script(
            "window.open('');")  # execute_script(script, *args) -> this function synchronously executes JavaScript in the current window/frame.
        browser.switch_to.window(browser.window_handles[1])
        browser.get(link)
        sleep(uniform(4, 5))
        match_centre_button = browser.find_element_by_link_text("Match Centre")
        is_element_clickable(match_centre_button)
        match_centre_button.click()
        sleep(uniform(4, 5))
        try:
            browser.find_element_by_link_text("Preview")
        except NoSuchElementException:
            browser.close()
            sleep(uniform(2, 3))
            browser.switch_to.window(browser.window_handles[0])
            continue
        download_match()
        sleep(uniform(2, 3))
        browser.close()
        sleep(uniform(2, 3))
        browser.switch_to.window(browser.window_handles[0])
        sleep(uniform(2, 3))


def save_file(is_preview, html_code):
    """This function saves the html file with squad.

    :param is_preview: bool, defines that currant website contains preview squad or not
    :param html_code: str, contains html code od current downloaded website
    """
    global number_of_downloaded_matches, season
    if not is_preview:
        with open(f"Matches_Test\\{season}\\Match_{str(number_of_downloaded_matches + 1)}_squad.html", 'w',
                  encoding="utf-8") as file:
            file.write(str(html_code))
    else:
        with open(f"Matches_Test\\{season}\\Match_{str(number_of_downloaded_matches + 1)}_preview.html", 'w',
                  encoding="utf-8") as file:
            file.write(str(html_code))
            number_of_downloaded_matches += 1
    print(asctime(localtime()) + "    " + file.name + " saved!")


##### Script #####
print("Script started: " + asctime(localtime()))
browser.get(
    "https://www.whoscored.com/Regions/250/Tournaments/12/Europe-Champions-League")  # Program starts from this website
sleep(uniform(8, 10))
cookies_accept()
for current_season in ALL_SEASONS:  # all UEFA Champions League matches from all seasons are downloaded
    season = current_season.replace("/", "_")
    create_directory_for_files(season)
    select_season(current_season)
    select_stage("Champions League Group Stages")
    download_websites()
    select_stage("Champions League Final Stage")
    download_websites()
    print("Downloading season " + current_season + " complete.")
    sleep(uniform(8, 10))
browser.close()
print("Script done: " + asctime(localtime()))
