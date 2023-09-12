#!/usr/bin/env python3

import os
import re
import sys
import json

from time import sleep
sys.path.append('.')

from src.connection import request, parse_url

from bs4 import BeautifulSoup
from github import Github

urls = [
    # "https://browser.engineering/http.html",
    # "https://browser.engineering/graphics.html",
    # "https://browser.engineering/text.html",
    # "https://browser.engineering/html.html",
    # "https://browser.engineering/layout.html",
    "https://browser.engineering/styles.html"
]
def main():
    # GitHub credentials
    ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
    REPO_NAME = "Tadwork/experimental-browser"
    ISSUE_TITLE_PREFIX = "Exercise: "

    # Get the GitHub repository
    g = Github(ACCESS_TOKEN)
    repo = g.get_repo(REPO_NAME)
    exercises = []
    # Get the webpage content
    # url = "https://browser.engineering/layout.html"
    for url in urls:
        response, body = request(parse_url(url))

        # Parse the HTML and extract the Exercise sections
        soup = BeautifulSoup(body, "html.parser")
        chapter = soup.find(text=re.compile(r'Chapter')).text.replace("of","").strip()
        
        exercises_h1 = soup.find("h1", {"id": "exercises"})
        em_elements = exercises_h1.find_all_next("em")
        print(f"Found {len(em_elements)} exercises in {url}")
        exercise = {}
        # Create a new GitHub issue for each p element
        for em in em_elements:
            description_elem = em.parent
            description = description_elem.text
            while description_elem.next_sibling and description_elem.next_sibling.find("em")  == None:
                if description_elem.tagName() == "pre" or description_elem.tagName() == "code":
                    description += f"```{description_elem.next_sibling.text}```"
                else:
                    description += description_elem.next_sibling.text
                description_elem = description_elem.next_sibling
            title = f"{ISSUE_TITLE_PREFIX} {chapter} - {em.text}"
            exercise = {"title": title, "description": description.replace('\n',' '), "link": url + "#exercises"}
            exercises.append(exercise)
    for exercise in exercises:
        print(f"Creating issue: {exercise['title']}")
        repo.create_issue(
            title=exercise["title"],
            body=f"{exercise['description']}\n\n[Source]({exercise['link']})",
            labels=["exercise"],
        )
        # needed to avoid rate limits
        sleep(1)
    print(json.dumps(exercises, indent=4))
        
if __name__ == "__main__":
    main()