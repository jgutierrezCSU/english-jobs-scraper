from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import json
import localcred
import format_html_results
import pandas as pd
import requests
import json



def convert_to_numbs(str1, str2):
    """
    Convert distance and duration strings to numerical values.

    Args:
        str1 (str): The distance string.
        str2 (str): The duration string.

    Returns:
        tuple: A tuple containing the converted distance and duration.

    Note:
        If both str1 and str2 are equal to 1, the function returns (1, 1).

    """
    if str1 == 1 and str2 == 1:
        # If distance and duration are both 1, return (1, 1)
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
            # If minutes is less than 10, convert it to two digits
            hours = int(words[0])
            minutes = int(words[2])
            total_minutes = hours * 100 + int("%02d" % minutes)
        else:
            total_minutes = int(words[0]) * 100 + int(words[2])

    # If it's under an hour
    if len(words) == 2:
        total_minutes = int(words[0])

    return (num1, total_minutes)

# Docs https://developers.google.com/maps/documentation/javascript/distancematrix#transit_options
def get_distance(job_main_location, given_origin):
    """
    Get the distance and duration between two locations using the Google Maps Distance Matrix API.

    Args:
        job_main_location (str): The destination location.
        given_origin (str): The origin location.

    Returns:
        tuple: A tuple containing the distance and duration between the two locations.

    Note:
        If the API request fails or the distance/duration is not found in the response,
        the function returns (1, 1) as a default value.

    """
   
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
    """
    Convert a dictionary to an HTML table.

    Args:
        dictionary (dict): The dictionary to convert.

    Returns:
        str: The HTML representation of the dictionary as a table.

    """
    table_html = "<table>\n"
    for key, value in dictionary.items():
        # Add a new row to the table with key-value pairs
        table_html += f"<tr><td>{key}</td><td>{value}</td></tr>\n"
    table_html += "</table>"
    return table_html

def save_html_table(html_content, file_path):
    """
    Save HTML content to a file.

    Args:
        html_content (str): The HTML content to be saved.
        file_path (str): The file path to save the HTML content to.

    Returns:
        None

    Note:
        The function will overwrite the existing file if it already exists.

    """
    with open(file_path, "w") as file:
        # Open the file in write mode and write the HTML content to it
        file.write(html_content)

def separate_string_by_spaces(string):
    # Split the string by spaces
    word_list = string.split()

    # Capitalize the first letter of each word
    capitalized_words = [word.capitalize() for word in word_list]

    return capitalized_words


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
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
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
# print("Give origin for mapping:")
# given_origin = input()
# print("Sort by? (duration only option for now): ")
# sortby_choice = input()

#for TESTING
# num_pages_to_search=4
given_origin="Abstatt"
sortby_choice="duration"
exclude_words_lst=separate_string_by_spaces("manager lead head senior director management Teacher embedded consultant PhD Thesis")
print(exclude_words_lst)

# Site has 2 different elements we have to traverse , "row job js-job" and "row job jobinternal"
results = []
cities_calculated_dict={}
page_count=1
for page_count in range(num_pages_to_search):
    # Get job posts for "external" jobs (js-jobs)
    job_posts_jsjobs = soup.find_all("div", class_="row job js-job")
    
    # Get job posts for "jobinternal" jobs
    job_posts_jobinternal = soup.find_all("div", class_="row job jobinternal")

    # Combine the job posts from both types into a single list
    all_job_posts = job_posts_jsjobs + job_posts_jobinternal

    for post in all_job_posts:
        # Extract the desired information from each post
        title = post.find("h3" if "js-job" in post["class"] else "h2", class_="title").text.strip()
        #seperate title by words for comparison
        title_to_lst=separate_string_by_spaces(title)
        # print(title_to_lst," :::::")
        if any(word in exclude_words_lst for word in title_to_lst):
            continue  # Skip processing the current job post and move to the next iteration
        company = post.find("i", class_="fa-li fa fa-bank").find_next_sibling(string=True).strip()
        job_main_location = post.find("i", class_="fa-li fa fa-map-marker").find_next_sibling(string=True).strip()

        # check if city already in list
        if job_main_location not in cities_calculated_dict:
            distance, duration = -1,-1 #get_distance(job_main_location, given_origin)
            # First time calculating, make key value pair for later retrieval (value = tuple)
            cities_calculated_dict[job_main_location] = (distance, duration)
        else:
            # City already in list
            # Get city values (a tuple)
            distance_duration_tup = cities_calculated_dict[job_main_location]
            distance, duration = distance_duration_tup[0], distance_duration_tup[1]

        # remove string chars and convert to integers for sorting
        dist_km, dist_mins = -1,-1#convert_to_numbs(distance, duration)
        # if No route was found (returned any 1's), home office
        if distance == 1 and duration == 1:
            distance, duration = "Home Office", "Home Office"
        summary = post.find("div", class_="content").text.strip()
        link = post.a['href']
        
        if "js-job" in post["class"]:
            # For "external" jobs, convert relative links to absolute links
            link = urljoin(url, link)
        else:
            # For "jobinternal" jobs, prepend the base URL
            link = 'https://englishjobs.de' + link

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

    # Get data from the next page
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
      
df.to_csv("temp_data.csv", index=False)
# print(df)
format_html_results.create_html_file(df)

# save_html_table(combined_results, "output.html")
# Close the browser
driver.quit()
