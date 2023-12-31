"""
This is a simple HTTP client that can download a web page from a URL.
"""
import argparse
import logging
import logging.config
import tkinter as tk
logging.config.fileConfig("logging.config")
logger = logging.getLogger(name="root")

from src.window import Browser

WIDTH, HEIGHT = 800, 600

# https://browser.engineering/http.html

args = argparse.ArgumentParser()
args.add_argument("--url", help="The URL to download")


def main():
    """main function"""
    url = args.parse_args().url
    Browser(WIDTH, HEIGHT).load(url)
    tk.mainloop()


if __name__ == "__main__":
    main()
