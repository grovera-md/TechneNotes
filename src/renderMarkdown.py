from bs4 import BeautifulSoup
import re
import copy
import markdown
import dbRepository as dbRepo
import os

def replace_func(match):
    idString = match.group(1)
    try:
        # Check if noteDbId string is a valid integer number
        noteDbId = int(idString)
        # Check if a db record for noteDbId exists
        note = dbRepo.findNoteByDbId(noteDbId)
        markdownString = note.content

    except:
        # Note was not found - replace include-link with empty string
        markdownString = ''
        return markdownString

    else:
        return markdownString

def render(markdownString):
    if (len(markdownString)> 0):
        # Replace any include-link in the markdown content (e.g. [linkText](include/note/[id] "linkTitle"))
        regexPattern = r'^\[.*?\]\([ \t]*include/note/(\d+?)(?:[ \t]+".*?")?[ \t]*\)$'
        markdownString = re.sub(regexPattern, replace_func, markdownString, flags=re.MULTILINE)
        # Debug - Dump final markdown to txt file
        # with open("markdown_debug.txt", "w") as markdownDebugFile:
        #     markdownDebugFile.write(markdownString)
        #     markdownDebugFile.close()
        # Convert markdown to html
        htmlString = markdown.markdown(markdownString, extensions=['attr_list', 'fenced_code'])
        # inputTxtFile = open('input_html.txt', 'r')
        noSpacesHtmlString = re.sub('\s+(?=<)', '', htmlString)
        strippedHtmlString = noSpacesHtmlString.strip("\n")
        inputSoup = BeautifulSoup(strippedHtmlString, "lxml")

    else:
        inputSoup = None

    templateHtml = """
    <html>
        <head>
            <!-- Required meta tags -->
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <!-- CSS -->
            <link rel="stylesheet" href="webview-assets-folder/css/prism.css"/>
            <link rel="stylesheet" href="webview-assets-folder/css/video-overlay-v3.css"/>
            <link rel="stylesheet" type="text/css" href="webview-assets-folder/css/jquery.fancybox.min.css"/>
            <link rel="stylesheet" type="text/css" href="webview-assets-folder/css/justifiedGallery.min.css"/>
            <link rel="stylesheet" href="webview-assets-folder/css/css-webview.css"/>
        </head>
        <body>
            <div class="container">
            </div>
            <!-- Javascript -->
            <script src="webview-assets-folder/js/jquery-3.5.1.min.js"></script>
            <script type="text/javascript" src="webview-assets-folder/js/prism.js"></script>
            <script src="webview-assets-folder/js/jquery.fancybox.min.js"></script>
            <script src="webview-assets-folder/js/jquery.justifiedGallery.min.js"></script>
            <script type="text/javascript">
            $(document).ready(function() {
                $(".justified-gallery").justifiedGallery({
                    rowHeight: 200
                });

                $('[data-fancybox="gallery"]').fancybox({
                    animationEffect: "fade",
                    animationDuration: 550
                });
            });
            </script>
        </body>
    </html>
    """
    # Replace 'webview-assets-folder' in templateHtml with the corresponding path of the 'webview' folder in the installation folder
    webviewAssetsPath = os.getcwd() + "/webview"
    templateHtml = re.sub('webview-assets-folder', webviewAssetsPath, templateHtml)

    # Remove spaces and new-lines
    noSpacesTemplateHtml = re.sub('\s+(?=<)', '', templateHtml)
    strippedTemplateHtml = noSpacesTemplateHtml.strip("\n")
    soup = BeautifulSoup(strippedTemplateHtml, "lxml")
    container = soup.body.find("div", class_="container", recursive=False)

    # CurrentBlockIndex
    # 0 = Inside div.container (Root)(iterating over <div>, <pre>, <h*>, <p>, <ul>, <ol>, <li>, standard <img> and <a>)
    # 1 = Multiple centered images

    currentBlockIndex = 0
    currentContainerDiv = None

    if inputSoup:
        # Iterate over all tags
        for currentTag in inputSoup.html.body.children:

            # Debug
            # print(currentTag.name)

            # Verify that the current element is not already wrapped appropriately
            if currentTag.name != "div":  # or currentTag.get("class") != ["row"]:
                # Wrap it up depending on element type

                # Code blocks
                if currentTag.name == "pre":

                    # Create a copy of the currentTag to insert in the new document.
                    # Note: appending the original element would remove it from the source html, altering the for loop
                    clonedTag = copy.copy(currentTag)

                    # Create the appropriate container divs and append them to the new document container
                    container.append(clonedTag)

                # Images
                # Can contain simple images, images with link, .gallery, .video, .sci, .mci, .fwi images.
                elif currentTag.name == "p" and (len(currentTag.get_text().strip()) == 0) and not currentTag.find("a", class_="jig", recursive=False):

                    # Note: Tag can either be an <a> or an <img>
                    for Tag in currentTag.children:

                        if currentBlockIndex != 0:
                            if (not Tag.get("class")) or (Tag.get("class") and "mci" not in Tag["class"]):
                                currentBlockIndex = 0
                                currentContainerDiv = None

                        # Create a copy of the currentTag to insert in the new document.
                        # Note: appending the original element would remove it from the source html, altering the for loop
                        clonedTag = copy.copy(Tag)

                        if Tag.get("class"):
                            # Remove redundant classes
                            if "gallery" in Tag["class"] and "video" in Tag["class"]:
                                Tag["class"].remove("gallery")

                            # If the element is an <a> tag with .gallery class
                            if Tag.name == "a" and "gallery" in Tag["class"]:
                                clonedTag["class"].remove("gallery")
                                # Add the 'data-fancybox' attribute
                                clonedTag['data-fancybox'] = "gallery"

                            # If the element is an <a> tag with .video class
                            elif Tag.name == "a" and "video" in Tag["class"]:
                                clonedTag["class"].remove("video")
                                # Add the 'data-fancybox' attribute
                                clonedTag['data-fancybox'] = "gallery"

                                # Wrap the <img> inside a <span> tag with .video-thumb-wrapper class
                                spanWrapper = soup.new_tag("span")
                                spanWrapper['class'] = ["video-thumb-wrapper"]
                                spanWrapper = clonedTag.img.wrap(spanWrapper)

                                # Append the <span.video-thumb-overlay> to the wrapper (after the <img>)
                                spanOverlay = soup.new_tag("span")
                                spanOverlay['class'] = ["video-thumb-overlay"]
                                svg = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" x="0px" y="0px" width="32px" height="32px" viewBox="0 0 32 32" enable-background="new 0 0 32 32" xml:space="preserve"> <g class="level-2"> <rect x="8.25" y="7.5" fill="#FFFFFF" width="15.5" height="16.75"></rect> </g> <g class="level-1"> <path fill="#444444" d="M30.662 5.003C26.174 4.358 21.214 4 16 4S5.826 4.358 1.338 5.003C0.478 8.369 0 12.089 0 16s0.477 7.63 1.338 10.997C5.827 27.643 10.786 28 16 28s10.174-0.357 14.662-1.003C31.521 23.631 32 19.911 32 16S31.523 8.37 30.662 5.003zM12 22V10l10 6L12 22z"></path> </g> </svg>'
                                svgSoup = BeautifulSoup(svg, "lxml")
                                spanOverlay.append(svgSoup)
                                spanWrapper.append(spanOverlay)

                            # Image with a link (<a><img/></a>)(No gallery or video) - Add target = _blank attribute.
                            elif Tag.name == "a" and "gallery" not in Tag["class"] and "video" not in Tag["class"]:
                                clonedTag['target'] = "_blank"
                                # print(str(clonedTag))

                            # Remove wrong classes (classes added without an <a> element)
                            elif Tag.name == "img":
                                if "gallery" in Tag["class"]:
                                    clonedTag["class"].remove("gallery")

                                if "video" in Tag["class"]:
                                    clonedTag["class"].remove("video")

                            else:
                                # do nothing
                                pass

                            # Check if the class attribute is now empty. If so, delete it.
                            if not clonedTag["class"]:
                                del clonedTag["class"]

                            if clonedTag.get("class") and (set(clonedTag["class"]) & {"sci", "mci", "fwi"}):

                                if "sci" in clonedTag["class"]:
                                    clonedTag["class"].remove("sci")
                                    # Check if the class attribute is now empty. If so, delete it.
                                    if not clonedTag["class"]:
                                        del clonedTag["class"]

                                    divSci = soup.new_tag("div")
                                    divSci['class'] = ["h-center"]
                                    container.append(clonedTag)
                                    clonedTag.wrap(divSci)

                                elif "mci" in clonedTag["class"]:
                                    clonedTag["class"].remove("mci")
                                    # Check if the class attribute is now empty. If so, delete it.
                                    if not clonedTag["class"]:
                                        del clonedTag["class"]

                                    # Check if previous element was already an .mci
                                    if currentBlockIndex == 1:
                                        # no clonedTag wrapping necessary
                                        currentContainerDiv.append(clonedTag)

                                    else:
                                        # Set the new currentBlockIndex
                                        currentBlockIndex = 1

                                        # Create the new .mci wrapper
                                        divMci = soup.new_tag("div")
                                        divMci['class'] = ["h-center"]
                                        container.append(clonedTag)
                                        # Wrap and set the new currentContainerDiv
                                        currentContainerDiv = clonedTag.wrap(divMci)

                                elif "fwi" in clonedTag["class"]:
                                    clonedTag["class"].remove("fwi")
                                    # Check if the class attribute is now empty. If so, delete it.
                                    if not clonedTag["class"]:
                                        del clonedTag["class"]

                                    divFwi = soup.new_tag("div")
                                    divFwi['class'] = ["full-width"]
                                    container.append(clonedTag)
                                    clonedTag.wrap(divFwi)

                                else:
                                    # do nothing
                                    pass

                            else:
                                container.append(clonedTag)

                        else:
                            # Tag has no class (so no .gallery or .video item)
                            # Check if Tag is an image WITH a link (<a><img/></a>) and add target = _blank attribute.
                            if Tag.name == "a":
                                clonedTag['target'] = "_blank"
                                # print(str(clonedTag))

                            container.append(clonedTag)

                    # Reset currentBlockIndex and currentContainerDiv
                    currentBlockIndex = 0
                    currentContainerDiv = None

                # Justified image gallery
                # Note: Fancybox will be added by default. Images MUST have a link (otherwise they will be ignored/skipped)
                elif currentTag.name == "p" and currentTag.find("a", class_="jig", recursive=False):

                    # Create the appropriate container divs and append them to the new document container
                    divJig = soup.new_tag("div")
                    divJig['class'] = ["justified-gallery"]

                    for aTag in currentTag.children:

                        # Create a copy of the currentTag to insert in the new document.
                        # Note: appending the original element would remove it from the source html, altering the for loop
                        clonedTag = copy.copy(aTag)

                        # Add the 'data-fancybox' attribute
                        clonedTag['data-fancybox'] = "gallery"

                        # Only <a> elements are accepted because each <img> must have a link for the gallery
                        if aTag.name == "a":
                            # Remove the .jig class from any item and add the data-fancybox = "gallery" attribute
                            if aTag.get("class"):
                                if "jig" in aTag["class"]:
                                    clonedTag["class"].remove("jig")
                                    # Check if the class attribute is now empty. If so, delete it.
                                    if not clonedTag["class"]:
                                        del clonedTag["class"]

                                if "video" in aTag["class"]:
                                    clonedTag["class"].remove("video")
                                    # Check if the class attribute is now empty. If so, delete it.
                                    if not clonedTag["class"]:
                                        del clonedTag["class"]

                                    # Wrap the <img> inside a <span> tag with .video-thumb-wrapper class
                                    spanWrapper = soup.new_tag("span")
                                    spanWrapper['class'] = ["video-thumb-wrapper"]
                                    spanWrapper = clonedTag.img.wrap(spanWrapper)

                                    # Append the <span.video-thumb-overlay> to the wrapper (after the <img>)
                                    spanOverlay = soup.new_tag("span")
                                    spanOverlay['class'] = ["video-thumb-overlay"]
                                    svg = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" x="0px" y="0px" width="32px" height="32px" viewBox="0 0 32 32" enable-background="new 0 0 32 32" xml:space="preserve"> <g class="level-2"> <rect x="8.25" y="7.5" fill="#FFFFFF" width="15.5" height="16.75"></rect> </g> <g class="level-1"> <path fill="#444444" d="M30.662 5.003C26.174 4.358 21.214 4 16 4S5.826 4.358 1.338 5.003C0.478 8.369 0 12.089 0 16s0.477 7.63 1.338 10.997C5.827 27.643 10.786 28 16 28s10.174-0.357 14.662-1.003C31.521 23.631 32 19.911 32 16S31.523 8.37 30.662 5.003zM12 22V10l10 6L12 22z"></path> </g> </svg>'
                                    svgSoup = BeautifulSoup(svg, "lxml")
                                    spanOverlay.append(svgSoup)
                                    spanWrapper.append(spanOverlay)

                            # Add the new item
                            divJig.append(clonedTag)

                    container.append(divJig)

                # Generic text elements (<h*>, <p>, <ul>, <ol>, <li>)
                else:
                    clonedTag = copy.copy(currentTag)

                    # Check if the currentTag contains an <a> tag (recursive=True to find nested <a> tags - e.g. <ul><li>text<a href=""></a></li></ul>)
                    if clonedTag.find("a", recursive=True):
                        # Add target=_blank attribute to all <a> elements, except for internal bookmark links (href="#id")
                        customKey, customValue = 'target', '_blank'
                        for aTag in clonedTag.find_all("a", recursive=True):
                            if 'href' in aTag.attrs:
                                aTagHref = aTag['href']
                                if len(aTagHref) > 0 and aTagHref[0:1] != '#' and not(customKey in aTag.attrs and customValue == aTag.attrs[customKey]):
                                    aTag['target'] = "_blank"

                            # print(str(aTag))

                    # Append the new item to the container Div
                    container.append(clonedTag)

            else:
                # Current element is a <div>. Directly add it to the html.

                # Create a copy of the currentTag to insert in the new document.
                # Note: appending the original element would remove it from the source html, altering the for loop
                clonedTag = copy.copy(currentTag)

                container.append(clonedTag)

    else:
        # newNoteMessage = soup.new_tag("p")
        # newNoteMessage.string = 'No content yet. Write something'
        # container.append(newNoteMessage)

        divSci = soup.new_tag("div")
        divSci['class'] = ["h-center"]
        startImg = soup.new_tag("img", src=webviewAssetsPath + "/images/startCoding.png")
        divSci.append(startImg)
        container.append(divSci)

        divSci2 = soup.new_tag("div")
        divSci2['class'] = ["h-center"]
        startContent = '<h2>Start coding to create a new multimedia note</h2><p>Look at the sample note to learn how to use Markdown elements.</p><p>Then, use the <code>Edit/Render</code> menu to render the page or press the <code>Ctrl+R</code> shortcut</p>'
        divSci2.append(BeautifulSoup(startContent, 'lxml'))
        container.append(divSci2)

    htmlPrettified = soup.prettify()
    htmlBrCorrected = re.sub(r"\s*\n\s*<code>\s*\n\s*(.+)\s*\n\s*</code>\s*\n\s*", r" <code>\1</code> ", htmlPrettified)

    # Debug
    # outputHtmlFile = open('outputHtml.txt', 'w')
    # outputHtmlFile.write(htmlBrCorrected)
    # outputHtmlFile.close()

    return htmlBrCorrected
