import time
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

# Create your views here.


@api_view(['GET'])
def scrape_linkedin(request):

    response = {}

    if request.method == "GET":
        username = request.data.get('username')
        password = request.data.get('password')
        print("Username : ", username)
        print("Password : ", password)

        if not username and not password:
            response['message'] = "Username and password are required"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        elif not username:
            response['message'] = "Username is required"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        elif not password:
            response['message'] = "Password is required"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        else:
            url = "https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin"
            driver = webdriver.Chrome()
            driver.get(url)
            # Implicit Wait Command
            driver.implicitly_wait(3)
            # Explicit Wait command
            wait = WebDriverWait(driver, 3)
            # Getting main window handle for controlling active window
            main_handle = driver.current_window_handle

            # Enter Username
            element = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@id='username']")))
            element.clear()
            element.send_keys(username)

            # Enter Password
            element = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@id='password']")))
            element.clear()
            element.send_keys(password)

            # Click Sign In Button
            signin_btn = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[@type='submit']")))
            signin_btn.click()

            # Click My Network
            my_network = wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@id='mynetwork-nav-item']")))
            my_network.click()

            # Get Total Connections and convert it to integer
            connect_val = wait.until(
                EC.visibility_of_element_located((By.XPATH, "//a[@data-control-name='connections']/div/div[2]")))
            total_connections = connect_val.text
            total_connections = int(total_connections.replace(',', ''))
            print("Total Connections : ", total_connections)

            # Click Connections
            connections = wait.until(
                EC.visibility_of_element_located((By.XPATH, "//a[@data-control-name='connections'][1]")))
            connections.click()

            # Open new window, save new window handle and jump back to main window
            driver.execute_script("window.open('')")
            driver.switch_to.window(driver.window_handles[-1])
            # Getting second window handle for controlling active window
            sub_handle = driver.current_window_handle
            driver.switch_to.window(main_handle)

            connections_list = {}

            # Get Connections list and loop over each connection and get its name, company name, email and save to csv file
            for i in range(1, 2):
                print(i)
                connections = driver.find_elements(By.XPATH, "//li[@class='list-style-none']")

                # Trying to see if the index is in current list, if not use javascript to scroll page and expand connections list
                try:
                    connection = driver.find_element(By.XPATH, "//li[@class='list-style-none'][{}]/div/a".format(i))
                except:
                    print("page scroll exception")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0)")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)

                connection = driver.find_element(By.XPATH, "//li[@class='list-style-none'][{}]/div/a".format(i))
                link = connection.get_attribute('href')

                driver.switch_to.window(sub_handle)
                driver.get(link)

                # Get Name
                name = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='flex-1 mr5']/ul/li")))
                name = name.text
                print(name)

                # Get Company Name
                try:
                    company = wait.until(EC.visibility_of_element_located(
                        (By.XPATH, "//ul[@class='pv-top-card--experience-list']/li/a/span[1]")))
                    company = company.text
                except:
                    company = None

                print(company)

                # Click Contact Info
                connections = wait.until(
                    EC.visibility_of_element_located((By.XPATH, "//a[@data-control-name='contact_see_more']")))
                connections.click()

                # Get email if available
                popup = wait.until(
                    EC.visibility_of_element_located((By.XPATH, "//h2[@class='pv-profile-section__card-heading mb4']")))
                try:
                    email = wait.until(EC.visibility_of_element_located(
                        (By.XPATH, "//section[@class='pv-contact-info__contact-type ci-email']/div/a")))
                    email = email.text
                except:
                    email = None

                print(email)

                # Saving Name, Company and Email to csv
                try:
                    connections_list[i] = {}
                    first_name = name.split()[0]
                    last_name = name.split()[-1]
                    connections_list[i]['first_name'] = first_name
                    connections_list[i]['last_name'] = last_name
                    connections_list[i]['company'] = company
                    connections_list[i]['email'] = email


                    # df = pd.DataFrame([[first_name, last_name, company, email]])
                    # with open('my_connections.csv', 'a', newline='\n') as f:
                    #     df.to_csv(f, index=False, header=False)

                except:
                    pass

                # Switch to main window
                driver.switch_to.window(main_handle)

            # Click on My Profile Button
            myprofile = wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@id='profile-nav-item']")))
            myprofile.click()

            # Click Sign Out
            signout = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[text()='Sign out']")))
            signout.click()

            # Close Browser
            driver.quit()

            response['message'] = "Crawling Successful"
            response['connections'] = connections_list

            return Response(response, status=status.HTTP_200_OK)

    else:
        response["message"] = "Only GET method is allowed"
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

