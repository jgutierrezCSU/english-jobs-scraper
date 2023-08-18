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
import requests
import json


def convert_to_numbs(str1, str2):
    if str1 == 1 and str2 == 1:
        return (1, 1)

    # Remove all non-numeric and non-decimal point characters from str1
    # and convert it to a float
    num1 = float("".join(filter(lambda x: x.isdigit() or x == ".", str1)))

    # Split the time string into a list of words
    words = str2.split()

    # Check if "mins" is less than 10, and convert the "hour" and "mins"
    # strings to integers
    if len(words) == 4:
        if int(words[2]) < 10:
            hours = int(words[0])
            minutes = int(words[2])
            total_minutes = hours * 100 + int("%02d" % minutes)
        else:
            total_minutes = int(words[0]) * 100 + int(words[2])

    # If it's under an hour
    if len(words) == 2:
        total_minutes = int(words[0])

    return (num1, total_minutes)


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

    # Check if the response status is OK
    if response_json["status"] == "OK":
        # Check if the 'distance' key exists in the response
        if 'distance' in response_json["rows"][0]["elements"][0]:
            distance = response_json["rows"][0]["elements"][0]["distance"]["text"]
        else:
            print("Distance not found in API response")
            return 1, 1

        # Check if the 'duration' key exists in the response
        if 'duration' in response_json["rows"][0]["elements"][0]:
            duration = response_json["rows"][0]["elements"][0]["duration"]["text"]
        else:
            print("Duration not found in API response")
            return 1, 1

        return distance, duration
    else:
        # Print an error message and return None for distance and duration
        print("Error: {}".format(response_json["status"]))
        return 1, 1
    
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
# Remove error logs
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
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
# Get number of pages to traverse
all_jobs_found = int(soup.find("span", class_="count").text.strip())
total_num_of_pages = all_jobs_found / 20
print("Number of pages available:", total_num_of_pages)
print("Enter number of pages to search (20 per page): ")
num_pages_to_search = int(input())
print("Give origin for mapping:")
given_origin = input()
print("Sort by? (duration only option for now): ")
sortby_choice = input()

# Site has 2 different elements we have to traverse , "row job js-job" and "row job jobinternal"
results = []
cities_calculated_dict={}
page_count=1
for page_count in range(num_pages_to_search):
    # js-jobs or "external" jobs have h3 title tags
    job_posts_jsjobs = soup.find_all("div", class_="row job js-job")
    for post in job_posts_jsjobs:
        # Extract the desired information from each post
        title = post.find("h3", class_="title").text.strip()
        company = post.find("i", class_="fa-li fa fa-bank").find_next_sibling(string=True).strip()
        job_main_location = post.find("i", class_="fa-li fa fa-map-marker").find_next_sibling(string=True).strip()

        # check if city already in list
        if job_main_location not in cities_calculated_dict:
            distance, duration = get_distance(job_main_location, given_origin)
            # First time calculating, make key value pair for later retrieval (value = tuple)
            cities_calculated_dict[job_main_location] = (distance, duration)
        else:
            # City already in list
            # Get city values (a tuple)
            distance_duration_tup = cities_calculated_dict[job_main_location]
            distance, duration = distance_duration_tup[0], distance_duration_tup[1]

        # remove string chars and convert to integers for sorting
        dist_km, dist_mins = convert_to_numbs(distance, duration)
        # if No route was found (returned any 1's), home office
        if distance == 1 and duration == 1:
            distance, duration = "Home Office", "Home Office"
        summary = post.find("div", class_="content").text.strip()
        link = post.a['href']
        # Convert relative links to absolute links
        link = urljoin(url, link)

        # Create a dictionary for the current post
        post_dict = {
            "title": title,
            "company": company,
            "location": job_main_location,
            "distance": distance,
            "duration": duration,
            "duration_for_sorting": dist_mins,
            "summary": summary,
            "link": link
        }

        # Append the dictionary to the results list
        results.append(post_dict)

    # jobinternal titles have h2 elements
    job_posts_jobinternal = soup.find_all("div", class_="row job jobinternal")
    for post in job_posts_jobinternal:
        # Extract the desired information from each post
        title = post.find("h2", class_="title").text.strip()
        company = post.find("i", class_="fa-li fa fa-bank").find_next_sibling(string=True).strip()
        job_main_location = post.find("i", class_="fa-li fa fa-map-marker").find_next_sibling(string=True).strip()

        # check if city already in list
        if job_main_location not in cities_calculated_dict:
            distance, duration = get_distance(job_main_location, given_origin)
            # First time calculating, make key value pair for later retrieval (value = tuple)
            cities_calculated_dict[job_main_location] = (distance, duration)
        else:
            # City already in list
            # Get city values (a tuple)
            distance_duration_tup = cities_calculated_dict[job_main_location]
            distance, duration = distance_duration_tup[0], distance_duration_tup[1]

        # remove string chars and convert to integers for sorting
        dist_km, dist_mins = convert_to_numbs(distance, duration)
        # if No route was found (returned any 1's), home office
        if distance == 1 and duration == 1:
            distance, duration = "Home Office", "Home Office"
        summary = post.find("div", class_="content").text.strip()
        link = 'https://englishjobs.de' + post.a['href']

        # Convert relative links to absolute links
        link = urljoin(url, link)

        # Create a dictionary for the current post
        post_dict = {
            "title": title,
            "company": company,
            "location": job_main_location,
            "distance": distance,
            "duration": duration,
            "duration_for_sorting": dist_mins,
            "summary": summary,
            "link": link
        }

        # Append the dictionary to the results list
        results.append(post_dict)

    # get data from next page
    url = "https://englishjobs.de/in/baden-wuerttemberg?q=It&page=" + str(page_count + 1)
    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content, "html.parser")

df = pd.DataFrame(results)

#Sort Option given
if sortby_choice is not None:
    # Sort by given choice
    if sortby_choice == "duration":
        df = df.sort_values(["duration_for_sorting"], ascending=[True])
      
df.to_csv("temp_data22.csv", index=False)
# print(df)
format_html_results.create_html_file(df)

# save_html_table(combined_results, "output.html")
# Close the browser
driver.quit()
