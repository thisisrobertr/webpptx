# webpptx

This is a web API that takes XML-based PowerPoint presentations (.pptx) and extracts certain information from them to a convenient JSON object. Embedded media is extracted and sent as a ZIP archive.

---

## I. Prerequisites

1. Python 3.8+

2. The following Python modules: flask, python-pptx, lxml (a dependency of python-pptx), pillow (PIL for Python 3), and dotenv (python-dotenv in PIP)

3. At least 4 GB of available disk space

---

## II. Setup and Installation

1. Clone this GitHub repository and change into its directory:

   	 	git clone https://github.com/thisisrobertr/webpptx
		cd webpptx

#### Using a Virtual Environment

A virtual environment creates a Python environment separate from the system interpreter and package directories; it provides a sort of sandbox for a particular application. This step is optional, but it can help prevent conflicts between system packages and dependencies for this project. To create a venv, execute the following commands between steps 1 and 2:
		
		python3 -m venv venv/
		source venv/bin/activate
		
Note the `source` command: the activation script cannot be directly executed in the shell.

2. Install dependencies

   	   pip3 install flask
	   pip3 install python-pptx
	   pip3 install pillow
	   pip3 install python-dotenv
	   
Since lxml is a dependency of python-pptx, it will be installed along with it.

3. Either configure this to work in your cloud instance or web server, or run the development version like so:

   	  `python3 pptx-microservice.py`

With this command, the API will be accessible on localhost:5000. There are no command-line arguments which can be passed into the script. It also uses the built-in Flask web server, which is not a production-grade environment. Do not use this script in isolation in production.

---

## III. Using this Script

### Endpoints


- The `/upload` endpoint (POST, multipart/form-data, file must be in key named "pres", API authentication must be in key named "key", other files may have any names)
When given a PPTX presentation and image files for each slide, this will extract the GIFs from an animated PPTX and render them onto the PNGs from ConvertAPI. The request must include the API key, a PowerPoint presentation, and images of each slide. These image files can have any names, but the form keys containing them should be something sensible like "slide1," slide2," etc. - Python's `sorted()` function is used to match them to a slide in PowerPoint.  Please allow a few minutes for the process to complete before requesting results with the `/form-results` or `/animation-results` endpoints. The server will return a JSON object with the job ID - this is how requests can be matched with their results.

- The `/form-results` endpoint (GET, multipart/form-data for API authentication key)
This returns a ZIP file with subfolders named for the job IDs returned by `/upload` and containing two things: a text file named webpptx-metadata.json and the media files for the presentation associated with that job ID. Webpptx-metadata.json will contain the speaker notes, embedded video URLs, and aspect ratio of the presentation, as well as the locations of embedded audio and video files. These will be structured using arrays: each key will have an array, and each slide will have its own sub-array with the data for that slide. If a particular slide has no information, an empty array will be used. The media files will be named with the patten mediaN.[extension] and imageN.[extension], where N represents the order in which the files were added to the PowerPoint file. If there are no results available, the body of the response will be empty.

- The `/animation-results` endpoint (GET, multipart/form-data for API authentication key)
This returns a ZIP file with the same structure outlined for `/form-results` ; each subfolder will contain the animated GIF images of each slide. If a slide has no animations, the original PNG is used. It has the same behavior as `/form-results` when no results are available. Transparent backgrounds in animated GIFs will not be preserved, as the alpha channels are deleted. This works by pasting each frame of each GIF onto the still image of each slide, then combining each composite frame into a single GIF file. It returns a JSON object containing a job ID- processing takes place in a separate worker thread.

If the key name is invalid, a 400 bad request error will result. If the file is not a PPTX or cannot be read, "422 unprocessable entity" will result. The API key included in the request must be valid; otherwise, it will be rejected with a "403 Forbidden."

### Environment Variables

Environment variables can either be specified in the standard way or in a .env file. Both of the following must be set.

a. `API_KEY` : This is the string that all requests must contain to be processed. It must be set, or the program will exit

b. `TEMP_DIR` : This is used to control where temp files are placed. The program expects this to have a trailing slash.



---

## IV. Concerns and Notes

- If you stop this program, any temp files scheduled for cleanup will not be deleted - you will have to delete them manually.

- Windows support is not tested - it may or may not work.

- GIF is a bad and inefficient file format. However, the final results look good, and GIF is only used with presentations that already contained this format. Theoretically, the animation could be done with short, looping MPEGs, but that would enter the realm of video, making the matter substantially more complicated.

-   The alpa channel is always stripped from GIFs, removing transparency. Animated GIFs with transparent backgrounds usually exposed different parts of the background, which would reveal parts of the first frame throughout the animation- that would look terrible. However, the total lack of transparency means that GIFs placed close enough to text may cover it up with a white background.

---

## V. Useful Information About PowerPoint Files

### Distances

- Distances are given in DXA, which is 1/20 (0.05) pt. Thus, 1pt = 20dxa, 1 inch = 72pt = 1440dxa, and 1cm = 0.3937007874in = 566.929133856dxa. Font sizes are given in half-points to avoid non-integer values

### Data Structure and Format
- All PPTX files are just ZIP files with a few extra features. Any archive utility should be able to extract them, but files re-zipped with a normal archive utility may or may not work again in PowerPoint. Extracting the file, two items will be produced: a file named "[Content Types].xml", and a directory named "ppt". The latter of these will hold the contents of the file.

- All video, images, and audio will be stored in the directory ppt/media; audio and video files will be named  mediaN.[extension] and images imageN.[extension], where N is the order in which the file was added to the presentation. 

- Each slide will have a file stored in /ppt/slides/_rels/ named "slideN.xml.rels" containing all external references in the "Target" attribute of <Relationship> and/or <Relationships> tags.

---

## VI. Useful Information About GIF Files and How this Program Handles them

### Framerates

- GIF files can have custom and variable framerates; this quantity is expressed not in terms of frames per second but of delay between each frame (the unit is milliseconds). The composite GIFs for each slide, however, can only have one framerate shared by every animation. For slower GIFs, the same frame will be drawn multiple times at a higher framerate to compensate for this while allowing higher-speed animations to work.
