# Dive into Deep Learning EPUB

This repository contains instructions and utilities that I used to create a version of [Dive into Deep Learning](https://d2l.ai/) in EPUB format.

The resulting file can be downloaded from:

```bash
https : // library.bz / main / uploads /  9B9E13BF1AA85964CD936A4CF99AF51C
```

## Prerequisites

- A working installation of Python.
- A working installation of LaTeX.

## Instructions

1. Use [WebToEpub](https://github.com/dteviot/WebToEpub) to convert the website to EPUB format. In this version we used the flag `.mdl-tabs__panel:not(.is-active)` just to include the `PyTorch` portions of the book.
2. Rename the given EPUB file to ZIP format and extract it. This will contain all the HTML files and images of the EPUB.
3. Create a virtual environment and install dependencies.

    ````bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ````

4. Execute `latex-to-svg.py`. This script will convert all the LaTeX equations in the HTML files to SVG format. The script will look for all the HTML files in the `d2l` folder and convert any LaTeX equations it finds. The resulting SVG files will be saved in the directory specified by the user.

    Execute this command to see the necessary arguments for the script:

    ````bash
    python3 latex-to-svg.py -h
    ````

5. Make any modifications to the HTML files as needed. For example, I removed all links to the discussions and links to open the notebooks in Google Colab or AWS SageMaker. I also tweaked the CSS styles to have better code formatting.
6. Run the following command to create the resulting EPUB file:

    ````bash
    zip -rX "../dl2.epub" mimetype $(ls|xargs echo|sed 's/mimetype//g') -x \*.DS_Store -x \*.git\*
    ````
