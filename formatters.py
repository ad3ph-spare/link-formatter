import os
from config import config
import requests
from logger import logger

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI
from PyPDF2 import PdfReader
import ssl, urllib

USER = 'Artem'

client = OpenAI(
    api_key="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"
)

if not USER == 'Artem':
    service = Service("T:/Downloads/geckodriver-v0.36.0-win64/geckodriver.exe")

class ParsingFail(Exception):
    """Custom exception for parsing failures"""
    pass


def string_to_dict(text):
    '''Receives "key: `value`, key: `value`, ..." Returns {"key": "value", "key": "value", ...}'''
    lst = [item.split(": `") for item in text.split("`, ")]
    print(lst)
    data = dict(lst)  # Splits the text "key: value, key: value, ..." into dict
    for key in data:
        data[key] = data[key].strip("`")  # Remove backticks
    return data

def test_string_to_dict():
    test_text = "title: `Test Title: Lololoshka, And Ryba`, author: `John Doe, Misha Joe`, date: `2023-10-01`"
    expected_output = {
        "title": "Test Title: Lololoshka, And Ryba",
        "author": "John Doe, Misha Joe",
        "date": "2023-10-01"
    }
    assert string_to_dict(test_text) == expected_output, "string_to_dict function failed"
test_string_to_dict()  # Run the test to ensure the function works correctly

def get_citation_json(link):
    assert "doi.org" in link or "dx.doi" in link, "Link must be a DOI link"
    headers = {"Accept": "application/vnd.citationstyles.csl+json, application/rdf+xml"}
    response = requests.get(link, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch data from {link}, status code: {response.status_code}"
        )
    return response.json()


def get_youtube_info(link):
    assert "youtu.be" in link or "youtube.com" in link, "Link must be a YouTube link"
    video_id = (
        link.split("watch?v=")[1].split("&")[0]
        if "watch?v=" in link
        else link.split("/")[-1]
    )
    if "?" in video_id:
        video_id = video_id.split("?")[0]
    api_key = "AIzaSyBvZoBOaT78gOjIl-G2_W-4ZjZtfVO6Jm4"
    response = requests.get(
        f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet,contentDetails,statistics,status"
    )
    return response.json()


def shorten_name(name: str) -> str:
    """Shortens a given name to the first letter of the first name and the full last name"""
    if name in ("de", "van", "von", "la", "le", "du"):
        return name

    if "-" in name:
        parts = name.split("-")
        return f"{parts[0][0]}.-{parts[1][0]}. "

    return f"{name[0]}. "


def get_site_info(link):
    if USER == 'Artem':
        driver = webdriver.Firefox()
    else:
        driver = webdriver.Firefox(service=service)
        
    body_text = None
    logger.debug("Opening link in firefox...")
    try:
        driver.get(link)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        conf = input(
            "Page loaded, please, type 'y' when content is ready for parsing: "
        )
        if conf != "y":
            logger.info("Operation aborted")
            raise RuntimeError("Aborted")

        body_element = driver.find_element(By.TAG_NAME, "body")
        body_text = body_element.text
    except:
        logger.error("Something went wrong")
    finally:
        driver.quit()
    if body_text is None:
        logger.error("Loading site error")
        return
    logger.debug("Body obtained, asking DeepSeek for parsing...")

    api_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-903183d640c34124b751afb0860e5f93",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "I will provide you with html page with an article and your task will be to extract data from it. You should extract data such as title, author of article, publication date. Your response should be formatted STRICTLY as following: 'title: `ARTICLE_TITLE`, author: `ARTICLE_AUTHOR`, date: `ARTICLE_DATE`'. Your answer should not contain any additional text, if you can't find some information pass '-' sign in the field.",
            },
            {"role": "user", "content": body_text},
        ],
        "temperature": 0.7,  # Adjust creativity (0-1)
    }
    response = requests.post(api_url, json=data, headers=headers)
    if response.status_code != 200:
        logger.error("DeepSeek request failed")
        return
    text = response.json()["choices"][0]["message"]["content"]
    logger.debug(f"DeepSeek response: {text}")
    # building the response dictionary
    try:
        data = string_to_dict(text)
        data["link"] = link
        return data
    
    except Exception as e:
        logger.error(f"DeepSeek parsing error: {e}")
        return {"title": "ERROR", "author": "ERROR", "date": "ERROR", "link": link}

def parse_citation_data(data, link, ret):
    authors = data["author"]
    authors_lst = []
    for j, author in enumerate(authors):
        if j > 2:
            authors_lst[-1] = " et al"
            break
        try:
            given = author.get("given").split(" ")
            authors_lst.append(
                "".join([shorten_name(given[i]) for i in range(len(given))])
            )
            family = author.get("family")
            authors_lst.append(f"{family}")
            if len(authors) > 1 and j == len(authors) - 2:
                authors_lst.append(" and ")
            elif j == len(authors) - 1:
                pass
            else:
                authors_lst.append(", ")
        except Exception as e:
            raise ParsingFail
    ret["authors"] = "".join(authors_lst).strip()
    ret["title"] = data.get("title")
    try:
        ret["journal"] = data.get(
            "container-title-short", data["container-title"]
        )
        ret["issue"] = data.get("journal-issue", {})["issue"]
        ret["vol"] = data.get("volume", "ERROR Volume")
        ret["page"] = data.get("page", "ERROR Page")
        ret["year"] = (
            data.get("journal-issue", {})
            .get("published-print", {})
            .get("date-parts", [[None]])[0][0]
        )
        if ret["year"] is None:
            ret["year"] = data.get("published", {}).get("date-parts", [[None]])[0][0]
    except:
        raise ParsingFail
    ret["link"] = link
    return ret


def llm_parse_citation_data(data: dict, link: str, ret: dict) -> dict:
    # makes a request to LLM to parse the citation data
    logger.warning("LLM parsing citation data")
    api_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-903183d640c34124b751afb0860e5f93",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": """I will provide you with a dictionary describing a journal article citation and your task will be to extract data from it.
                You should extract data such as title, authors, short journal name, issue, volume, pages and year. Your response should be formatted STRICTLY as following: 
                title: `ARTICLE_TITLE`, authors: `ARTICLE_AUTHORS`, journal: `JOURNAL`, issue: `ISSUE`, vol: `VOL`, page: `PAGE`, year: `YEAR`.
                Your answer should not contain any additional text, if you can't find some information pass ERROR in the field. Leave the backticks around every data field in the response. Shorten the authors names to the first letter of the first name and full last name, e.g. "John Smith" -> "J. Smith".
                """,
            },
            {"role": "user", "content": str(data)},
        ],
        "temperature": 0.7,  # Adjust creativity (0-1)
    }
    
    response = requests.post(api_url, json=data, headers=headers)
    if response.status_code != 200:
        logger.error("DeepSeek answer incorrect")
        return
    text = response.json()["choices"][0]["message"]["content"]
    print(text)
    input()
    try:
        data = string_to_dict(text)
        data["link"] = link
        return data
    except Exception as e:
        logger.error(f"LLM parsing error: {e}")
        return {"authors": "ERROR", "title": "ERROR", "journal": "ERROR", "issue": "ERROR", "vol": "ERROR", "page": "ERROR", "year": "ERROR", "link": link}

def insert_values(object_type, link, format_string):
    """[fields]
    video = title, source, channel, date, link
    paper = authors, title, journal, issue, vol, page year, link
    site = title, author, site, date, link
    wikipedia = title, link
    reels = title, source, channel, date, link
    book = authors, title, publisher, year
    archive_iypt = problem, year, reporter, team"""
    config_fields = config["fields"][object_type]

    ret = {key: f"%%{key}%%" for key in config_fields.split(", ")}

    # requests to the link to get the data and processing/parsing/llm api calls
    match object_type:
        case "video":
            data = get_youtube_info(link)
            if not data.get("items"):
                logger.error(f"Error fetching video data")
                return f"ERROR fetching video data\t link: {link}"
            snippet = data["items"][0]["snippet"]
            ret["title"] = snippet["title"]
            ret["source"] = "YouTube"
            ret["channel"] = snippet["channelTitle"]
            published_at = snippet["publishedAt"]
            ret["date"] = ".".join(published_at.split("T")[0].split("-")[::-1])
            ret["link"] = link
            
            
        case "paper":
            try:
                data = get_citation_json(link)
            except Exception as e:
                logger.error(f"Error fetching citation data: {e}")
                return "ERROR fetching citation data"
            try:
                ret = parse_citation_data(data, link, ret)
            except ParsingFail:
                ret = llm_parse_citation_data(data, link, ret)
                
                            
        case "site":
            ret = get_site_info(link)
        
        
        case "wikipedia":
            ret["title"] = link.split("/")[-1].replace("_", " ")
            ret["link"] = link
            
            
        case "book":
            logger.warning(f"book is unsupported for now, skipping")
            
        case "file":
            logger.info(f"Downloading '{link}'...")
            ssl._create_default_https_context = ssl._create_unverified_context
            ssl_context = ssl._create_unverified_context()
            if not os.path.exists("./tmp"):
                os.makedirs("./tmp")
            try:
                with urllib.request.urlopen(link, context=ssl_context) as response:
                    with open("./tmp/downloaded.pdf", "wb") as out_file:
                        out_file.write(response.read())
            except:
                logger.error("Download error. Trying thruogh browser")
                if USER == "Artem":
                    driver = webdriver.Firefox()
                else:
                    driver = webdriver.Firefox(service=service)
                logger.debug("Opening link in firefox...")
                try:
                    driver.get(link)

                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    conf = input(
                        "Page loadded, please, copy downloaded file in tmp folder and rename it to 'donwloaded.pdf'. type 'y' when you done: "
                    )
                    if conf != "y":
                        logger.info("Operation aborted")
                        raise RuntimeError("Aborted")
                except:
                    logger.error("Something went wrong")
                    return f"ERROR downloading\tlink: {link}"
                finally:
                    driver.quit()
            pdf_path = "./tmp/downloaded.pdf"
            reader = PdfReader(pdf_path)
            text = ""
            
            total_pages = len(reader.pages)
            # read only first three and the last one page
            pages_to_read = [0, 1, 2, total_pages - 1] if total_pages > 3 else range(total_pages)
            
            for j, page in enumerate(reader.pages):
                if j not in pages_to_read:
                    continue
                text += page.extract_text() + "\n"
            headers = {
                "Authorization": "Bearer sk-903183d640c34124b751afb0860e5f93",
                "Content-Type": "application/json",
            }
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": """I will provide you with pdf page with an article and your task will be to extract data from it. You should extract such data as title and author of article and also a publication date. 
                        Your response should be formatted STRICTLY as following: title: `ARTICLE_TITLE`, author: `ARTICLE_AUTHOR`, date: `ARTICLE_DATE`. You answer should not contain any additional text, if you can't find some information pass '-' sign in the field. Preserve the backticks around the values. Correct the all-capitals if necessary. Shorten authors names (if Firstname Lastname is provided, write F. Lastname)""",
                    },
                    {"role": "user", "content": text},
                ],
                "temperature": 0.7,  # Adjust creativity (0-1)
            }
            api_url = "https://api.deepseek.com/v1/chat/completions"
            
            response = requests.post(api_url, json=data, headers=headers)
            if response.status_code != 200:
                logger.error("DeepSeek request failed")
                return f"ERROR parsing data\tlink: {link}"
            text = response.json()["choices"][0]["message"]["content"]
            data = string_to_dict(text)
            data["link"] = link
            ret = data
            
        case "archive_iypt":
            logger.warning(f"archive_iypt is unsupported fro now, skipping")
            
            
    return format_string.format(**ret)


def format_link(object_type, link):
    if object_type in config["output_formats"]:
        return insert_values(object_type, link, config["output_formats"][object_type])
    return link
