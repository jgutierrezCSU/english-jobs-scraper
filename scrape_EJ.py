from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import json
import localcred
import format_html_results
import pandas as pd


# Docs https://developers.google.com/maps/documentation/javascript/distancematrix#transit_options
# mode options: BICYCLING ,DRIVING ,TRANSIT (public transit routes.),WALKING
def get_distance(job_main_location, given_origin):

    # Set up the URL for the Google Maps Distance Matrix API request
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric"
    url += "&origins={}".format(given_origin)
    url += "&destinations={}".format(job_main_location)
    url += "&mode=DRIVING"
    url += "&key={}".format(localcred.API_KEY)

    # Make the API request and parse the response
    response = requests.get(url)
    response_json = json.loads(response.text)

    # Check if the response status is OK and extract the distance and duration if so
    if response_json["status"] == "OK":
        distance = response_json["rows"][0]["elements"][0]["distance"]["text"]
        duration = response_json["rows"][0]["elements"][0]["duration"]["text"]
        return distance, duration
    else:
        # Print an error message and return None for distance and duration
        print("Error: {}".format(response_json["status"]))
        return None, None
    
def dict_to_html_table(dictionary):
    table_html = "<table>\n"
    for key, value in dictionary.items():
        table_html += f"<tr><td>{key}</td><td>{value}</td></tr>\n"
    table_html += "</table>"
    return table_html

def save_html_table(html_content, file_path):
    with open(file_path, "w") as file:
        file.write(html_content)




# Configure Chrome options for headless browsing
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# Set path to chromedriver executable as per your configuration
chromedriver_path = "./chromedriver"
# Set Chrome options and initialize the driver
driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
# URL to scrape
url = "https://englishjobs.de/in/baden-wuerttemberg?q=It"
# Perform scraping
driver.get(url)
# Extract desired information from the webpage
content = driver.page_source
soup = BeautifulSoup(content, "html.parser")
#get number of pages to travers 
all_jobs_found = int(soup.find("span", class_="count").text.strip())
total_num_of_pages =all_jobs_found/20
print("Number of pages available:", total_num_of_pages)
print("Enter number of pages to search (20 per page): ")
# num_pages_to_search = int(input())
num_pages_to_search = 2
given_origin="weinsberg"
sortby_choice="duration"

# Site has 2 different elements we have to traverse , "row job js-job" and "row job jobinternal"
results = []
page_count=1
for page_count in range(num_pages_to_search):
    #js-jobs or "external" jobs have h3 title tags
    job_posts_jsjobs = soup.find_all("div", class_="row job js-job")
    for post in job_posts_jsjobs:
        # Extract the desired information from each post
        title = post.find("h3", class_="title").text.strip()
        company = post.find("i", class_="fa-li fa fa-bank").find_next_sibling(text=True).strip()
        job_main_location = post.find("i", class_="fa-li fa fa-map-marker").find_next_sibling(text=True).strip()
        distance, duration = get_distance(job_main_location, given_origin)
        summary= post.find("div", class_="content").text.strip()
        link= post.a['href']
        # Convert relative links to absolute links
        link = urljoin(url, link)

        # Create a dictionary for the current post
        post_dict = {
            "title": title,
            "company": company,
            "location": job_main_location,
            "distance":distance,
            "duration":duration,
            "summary": summary,
            "link" : link
        }

        # Append the dictionary to the results list
        results.append(post_dict)

    #jobinternal titles have h2 elements
    job_posts_jobinternal = soup.find_all("div", class_="row job jobinternal")
    for post in job_posts_jobinternal:
        # Extract the desired information from each post
        title = post.find("h2", class_="title").text.strip()
        company = post.find("i", class_="fa-li fa fa-bank").find_next_sibling(text=True).strip()
        job_main_location = post.find("i", class_="fa-li fa fa-map-marker").find_next_sibling(text=True).strip()
        distance, duration = get_distance(job_main_location, given_origin)
        summary= post.find("div", class_="content").text.strip()
        link= 'https://englishjobs.de' + post.a['href']
        
        # Convert relative links to absolute links
        link = urljoin(url, link)

        # Create a dictionary for the current post
        post_dict = {
            "title": title,
            "company": company,
            "location": job_main_location,
            "distance":distance,
            "duration":duration,
            "summary": summary,
            "link" : link

        }

        # Append the dictionary to the results list
        results.append(post_dict)
    #get data from next page
    url = "https://englishjobs.de/in/baden-wuerttemberg?q=It&page="+ str(page_count+1)
    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content, "html.parser")




df = pd.DataFrame(results)
df.to_csv("temp_data.csv", index=False)
# print(df)
format_html_results.create_html_file(df)


# combined_results=""
# # Print the results
# for single_ad in results:
#     single_add_html=dict_to_html_table(single_ad)
#     combined_results = combined_results+ single_add_html + "<br>"+"<br>"



# save_html_table(combined_results, "output.html")
# Close the browser
driver.quit()
