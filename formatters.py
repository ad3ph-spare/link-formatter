from config import config
import requests

from logger import logger


def get_citation_json(link):
    assert "doi.org" in link or "dx.doi" in link, "Link must be a DOI link"
    headers = {"Accept": "application/vnd.citationstyles.csl+json, application/rdf+xml"}
    response = requests.get(link, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from {link}, status code: {response.status_code}")
    return response.json()

def get_youtube_info(link):
    assert "youtu.be" in link or "youtube.com" in link, "Link must be a YouTube link"
    video_id = link.split("youtu.be")[1].split["/"][0] if "youtu.be" in link else link.split("watch?v=")[1].split("&")[0]
    api_key = "AIzaSyBvZoBOaT78gOjIl-G2_W-4ZjZtfVO6Jm4"
    response = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet,contentDetails,statistics,status"
    return response.json()

def shorten_name(name: str) -> str:
    '''Shortens a given name to the first letter of the first name and the full last name'''
    if name in ("de", "van", "von", "la", "le", "du"):    
        return name
    
    if "-" in name:
        parts = name.split("-")
        return f"{parts[0][0]}.-{parts[1][0]}. "
    
    return f"{name[0]}. "

def insert_values(object_type, link, format_string):
    '''[fields]
    video = title, source, channel, date, link
    paper = authors, title, journal, issue, vol, page year
    site = title, author, site, date, link
    wikipedia = title, link
    reels = title, source, channel, date, link
    book = authors, title, publisher, year
    archive_iypt = problem, year, reporter, team'''
    config_fields = config['fields'][object_type]

    ret = {key: f"%%{key}%%" for key in config_fields.split(', ')}
    
    # requests to the link to get the data and processing/parsing/llm api calls
    match object_type:
        case 'video':
            data = get_youtube_info(link)
            
        case 'paper':
            try:
                data = get_citation_json(link)
            except Exception as e:
                logger.error(f"Error fetching citation data: {e}")
                return "ERROR fetching citation data"
            authors = data["author"]
            authors_lst = []
            for j, author in enumerate(authors):
                if j > 2:
                    authors_lst[-1] = " et al"
                    break
                try:
                    given = author.get("given").split(" ")
                    authors_lst.append("".join([shorten_name(given[i]) for i in range(len(given))]))
                    family = author.get("family")
                    authors_lst.append(f"{family}")
                    if len(authors) > 1 and j == len(authors) - 2:
                        authors_lst.append(" and ")
                    elif j == len(authors) - 1:
                        pass
                    else:
                        authors_lst.append(", ")
                except Exception as e:
                    logger.warning(f"Error processing author {author}: {e}")
                    authors_lst.append("ERROR Author")
            ret["authors"] = "".join(authors_lst).strip()
            ret["title"] = data.get("title")
            ret["journal"] = data.get("container-title-short", data.get("container-title", "ERROR Journal"))
            ret["issue"] = data.get("journal-issue", {}).get("issue", "ERROR Issue")
            ret["vol"] = data.get("volume", "ERROR Volume")
            ret["page"] = data.get("page", "ERROR Page")
            ret["year"] = data.get("journal-issue", {}).get("published-print", {}).get("date-parts", [[None]])[0][0]
            if ret["year"] is None:
                ret["year"] = data.get("published", {}).get("date-parts", [[None]])[0][0]
        case 'site':
            pass
        case 'wikipedia':
            ret["title"] = link.split('/')[-1].replace('_', ' ')
            ret["link"] = link
        case 'book':
            pass
        case 'archive_iypt':
            pass
    
    return format_string.format(**ret)

def format_link(object_type, link):
    if object_type in config['output_formats']:
        return insert_values(object_type, link, config['output_formats'][object_type])
    return link