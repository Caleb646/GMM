from django.conf import settings
from django.test import LiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


# Create your tests here.
class UserAdminTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_url = reverse("user:index")

    def thread_changelist(self):
        pass
        # selenium = webdriver.Chrome(
        #     "C:\Program Files\Google\Chrome\Application\chrome.exe"
        # )
        # # Choose your url to visit
        # selenium.get(f"{self.base_url}rfis/thread/")
        # # find the elements you need to submit form
        # print(selenium.current_url)
        # assert selenium.current_url == f"{self.base_url}user/login/"
        # player_name = selenium.find_element_by_id('id_name')
        # player_height = selenium.find_element_by_id('id_height')
        # player_team = selenium.find_element_by_id('id_team')
        # player_ppg = selenium.find_element_by_id('id_ppg')

        # submit = selenium.find_element_by_id('submit_button')

        # #populate the form with data
        # player_name.send_keys('Lebron James')
        # player_team.send_keys('Los Angeles Lakers')
        # player_height.send_keys('6 feet 9 inches')
        # player_ppg.send_keys('25.7')

        # #submit form
        # submit.send_keys(Keys.RETURN)

        # #check result; page source looks at entire html document
        # assert 'Lebron James' in selenium.page_source
