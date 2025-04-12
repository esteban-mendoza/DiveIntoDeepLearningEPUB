# Dive into Deep Learning EPUB

This repository contains instructions and utilities that I used to create a version of [Dive into Deep Learning](https://d2l.ai/) in EPUB format.

The resulting file can be downloaded from:

```bash
https://library.bz/main/uploads/23B34638B780F8D4BA87220FC82372CC
```

## Prerequisites

- A working installation of Python.
- A working installation of LaTeX.

## Instructions

1. Use [WebToEpub](https://github.com/dteviot/WebToEpub) to convert the website to EPUB format. In this version we used the flag 

    ````bash
    .mdl-tabs__panel:not(.is-active), .d2l-tabs, button
    ````

   just to include the `PyTorch` portions of the book and remove some annoying links.

   We also had to follow instructions in [this issue](https://github.com/dteviot/WebToEpub/issues/1798#issuecomment-2799026548) to retain useful links to previous and next chapters.

3. Rename the given EPUB file to ZIP format and extract it. This will contain all the HTML files and images of the EPUB.
4. Create a virtual environment and install dependencies.

    ````bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ````

5. Execute `latex-to-svg.py`. This script will convert all the LaTeX equations in the HTML files to SVG format. The script will look for all the HTML files in the `d2l` folder and convert any LaTeX equations it finds. The resulting SVG files will be saved in the directory specified by the user.

    Execute this command to see the necessary arguments for the script:

    ````bash
    python3 latex-to-svg.py -h
    ````

6. Make any modifications to the HTML files as needed. For example, I removed all links to the discussions and links to open the notebooks in Google Colab or AWS SageMaker. 

   I also tweaked the CSS styles to have better code and Math formatting by adding this to the CSS stylesheet:
   ````css
    /* Math */
    .math-image {
      vertical-align: middle;
      display: inline-block;
      height: 1.2em;
      margin: 0;
      padding: 0;
    }
    .math-display {
      text-align: center;
      margin: 1em 0;
      position: relative;
    }
    .math-display-image {
      max-width: 100%;
      height: auto;
      margin: 0 auto;
      display: block;
    }
    .eqno {
      position: absolute;
      right: 0;
      top: 50%;
      transform: translateY(-50%);
    }
    /* Code blocks styling for Kindle with reduced vertical spacing */
    .highlight-python, .highlight-bash, .highlight-default, .output {
      margin: 0; /* Remove default margins */
      padding: 0; /* Remove default padding */
    }
    
    .highlight {
      font-size: 80%; /* Reduce font size to 80% of normal text */
      line-height: 1.2; /* Tighter line spacing */
      margin: 0.2em 0; /* Minimal vertical margins */
      padding: 0.3em 0.5em; /* Reduced padding, especially vertical */
      background-color: #f5f5f5; /* Light gray background */
      border: 1px solid #ddd; /* Light border */
      overflow-x: auto; /* Allow horizontal scrolling if needed */
      white-space: pre-wrap; /* Allow wrapping of long lines */
      font-family: monospace; /* Use monospace font */
    }
    
    /* Target the container divs directly */
    div.highlight-python, div.highlight-bash, div.output {
      margin-top: 0.3em; /* Small top margin */
      margin-bottom: 0.3em; /* Small bottom margin */
    }
    
    /* Make output blocks slightly different */
    .output .highlight {
      background-color: #f8f8f8; /* Slightly different background for output */
      border-top: none; /* Remove top border if it follows code */
      padding-top: 0.2em; /* Less padding at top */
      padding-bottom: 0.2em; /* Less padding at bottom */
      font-style: italic; /* Make output italic to differentiate */
      margin-top: 0; /* No margin between code and its output */
    }
    
    /* Adjust span colors for better contrast on e-ink */
    .highlight .n { color: #000000; } /* Name - black */
    .highlight .o { font-weight: bold; } /* Operator - bold */
    .highlight .mi, .highlight .mf { color: #333333; } /* Numbers - dark gray */
    .highlight .s { font-style: italic; } /* Strings - italic */
    .highlight .k, .highlight .kn { font-weight: bold; } /* Keywords - bold */
    .highlight .c, .highlight .c1 { font-style: italic; color: #555555; } /* Comments - italic, gray */
    
    /* Make pre elements inside highlights fit better */
    .highlight pre {
      margin: 0;
      padding: 0;
      font-size: inherit;
      line-height: inherit;
    }
    
    /* Adjust spacing between code and output blocks */
    .highlight + .output {
      margin-top: -0.3em; /* Negative margin to pull output closer to code */
    }
    
    /* Ensure code blocks following paragraphs have appropriate spacing */
    p + .highlight-python, p + .highlight-bash {
      margin-top: 0.5em; /* Space after paragraph */
    }
    
    /* Ensure paragraphs following code blocks have appropriate spacing */
    .highlight-python + p, .highlight-bash + p, .output + p {
      margin-top: 0.5em; /* Space before next paragraph */
    }
   ````
 
7. Run the following command to create the resulting EPUB file:

    ````bash
    zip -rX "../dl2.epub" mimetype $(ls|xargs echo|sed 's/mimetype//g') -x \*.DS_Store -x \*.git\*
    ````
