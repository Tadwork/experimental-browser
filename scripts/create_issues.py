#!/usr/bin/env python3

import os
import re
import sys
from pprint import pprint
sys.path.append('.')

from src.connection import request, parse_url

from bs4 import BeautifulSoup
from github import Github

urls = [
    # "https://browser.engineering/http.html",
    # "https://browser.engineering/layout.html"
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
        response = request(parse_url(url))

        # Parse the HTML and extract the Exercise sections
        soup = BeautifulSoup(response.body, "html.parser")
        chapter = soup.find(text=re.compile(r'Chapter')).text.replace("of","").strip()
        
        exercises_h1 = soup.find("h1", {"id": "exercises"})
        p_elements = exercises_h1.find_all_next("p")
 
        exercise = {}
        # Create a new GitHub issue for each p element
        for p in p_elements:
            em = p.find("em")
            if not em:
                exercise["description"] += p.text
            if em is not None:
                if "title" in exercise:
                    exercises.append(exercise)
                title = f"{ISSUE_TITLE_PREFIX} {chapter} - {em.text}"
                body = p.text.replace(em.text, "").replace('\n','').strip()
                exercise = {"title": title, "description": body, "link": url + "#exercises"}
    # for exercise in exercises[1:]:
    #     print(f"Creating issue: {exercise['title']}")
    #     repo.create_issue(
    #         title=exercise["title"],
    #         body=f"{exercise['description']}\n[Source]({exercise['link']})",
    #         labels=["exercise"],
    #     )
    pprint(exercises)
        
if __name__ == "__main__":
    main()