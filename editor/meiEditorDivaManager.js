require(['meiEditor', 'https://x2js.googlecode.com/hg/xml2json.js'], function(){

(function ($)
{
    window.meiEditorPlugins.push((function()
    {
        var retval = 
            {
            divName: "diva-manager",
            title: 'Diva page manager',
            dropdownOptions: 
            {
                "Link files to Diva images...": "file-link-dropdown",
                "Unlink files from Diva images...": "file-unlink-dropdown",
                "Auto-link files by filename": "auto-link-dropdown",
                "Update Diva": "update-diva-dropdown",
                "Clear selection": "clear-selection-dropdown",
                "Help...": "diva-help-dropdown",
            },
            requiredSettings: ['divaInstance', 'jsonFileLocation'],
            init: function(meiEditor, meiEditorSettings)
            {
                $.extend(meiEditorSettings, 
                {
                    divaPageList: [], //list of active pages in Diva
                    divaImagesToMeiFiles: {}, //keeps track of linked files
                    neumeObjects: {}, //keeps track of neume objects
                    curOverlayBox: "",
                    initDragTop: "",
                    initDragLeft: "",
                });

                $("#file-link-dropdown").on('click', function()
                {
                    $('#fileLinkModal').modal();
                });

                $("#file-unlink-dropdown").on('click', function()
                {
                    $('#fileUnlinkModal').modal();
                });

                $("#auto-link-dropdown").on('click', function()
                {
                    meiEditor.autoLinkFiles();
                });

                $("#update-diva-dropdown").on('click', function()
                {
                    meiEditor.createHighlights();
                });

                $("#clear-selection-dropdown").on('click', function()
                {
                    meiEditor.deselectAllHighlights();
                });

                $("#diva-help-dropdown").on('click', function()
                {
                    $("#divaHelpModal").modal();
                });

                meiEditor.createModal("fileLinkModal", false, 
                    "<span class='modalSubLeft'>"
                    + "Select an MEI file:<br>"
                    + meiEditor.createSelect("file-link", meiEditorSettings.pageData)
                    + "</span>"
                    + "<span class='modalSubRight'>"
                    + "Select a Diva image:<br>"
                    + meiEditor.createSelect("diva-link", meiEditorSettings.divaPageList, true)
                    + "</span>"
                    + "<div class='clear'></div>"
                    + "<div class='centeredAccept'>"
                    + "<button id='link-files'>Link selected files</button>"
                    + "</div>"
                    );

                meiEditor.createModal("fileUnlinkModal", false, 
                    "<div id='unlink-wrapper'>"
                    + "Unlink an MEI file from a Diva file:<br>"
                    + "<select id='selectUnlink'></select><br>"
                    + "<button id='unlink-files'>Unlink selected files</button>"
                    + "</div>"
                    );

                meiEditor.createModal("divaHelpModal", false,
                    "<h2>Help</h2>"
                    + "<li>To get highlights from a file to show up in the Diva pane, click 'Link files to Diva images...' from the dropdown menu and select the files you want to link.</li>"
                    + "<br><li>'Auto-link files by filename' will automatically strip file extensions and try to match files so that '001.mei' and '001.tiff' become linked.</li>"
                    + "<br><li>Changes you make to the MEI document will not automatically transfer over; click 'Update Diva' to reload the highlighted objects in the image viewer.</li>"
                    + "<br><li>Clicking on a box then clicking on another will unselect the first one; to select multiple, hold shift and drag to select everything within a box or hold shift and click multiple.</li>"
                    + "<br><li>To deselect all highlights, choose the 'Clear selection' option of this dropdown.</li>"
                    + "<br><li>Press the 'delete' key on your keyboard to delete all selected highlights and the MEI lines associated with them.</li>"
                    );

                //the div that pops up when highlights are hovered over
                meiEditorSettings.element.append('<span id="hover-div"></span>'); 

                /*
                    Creates highlights based on the ACE documents.
                */
                meiEditor.createHighlights = function()
                {      
                    /*
                        Function called when sections are rehighlighted to refresh the listeners.
                    */
                    var reapplyHoverListener = function()
                    {
                        $(".overlay-box").hover(function(e) //when the hover starts for an overlay-box
                        {
                            currentTarget = e.target.id;

                            $("#hover-div").html(meiEditorSettings.neumeObjects[currentTarget] + "<br>Click to find in document.");
                            $("#hover-div").css(//create a div with the name of the hovered neume
                            {
                                'height': 'auto',
                                'top': e.pageY - 10,
                                'left': e.pageX + 10,
                                'padding-left': '10px',
                                'padding-right': '10px',
                                'border': 'thin black solid',
                                'background': '#FFFFFF',
                                'display': 'block',
                                'vertical-align': 'middle',
                            });

                            //if this isn't selected, change the color 
                            if(!$("#" + currentTarget).hasClass('selectedHover'))
                            {
                                $("#"+currentTarget).css('background-color', 'rgba(255, 255, 255, 0.05)');
                            }

                            $(document).on('mousemove', function(e) //have it follow the mouse
                            {
                                $("#hover-div").offset(
                                {
                                    'top': e.pageY - 10,
                                    'left': e.pageX + 10,
                                });
                            });
                        }, function(e)
                        {
                            currentTarget = e.target.id;
                            $(document).unbind('mousemove'); //stops moving the div
                            $("#hover-div").css('display', 'none'); //hides the div
                            $("#hover-div").html("");

                            //if this isn't selected, change the color back to normal
                            if(!$("#" + currentTarget).hasClass('selectedHover'))
                            {
                                $("#" + currentTarget).css('background-color', 'rgba(255, 0, 0, 0.2)');
                            }
                        });

                        $(".overlay-box").click(function(e)
                        {
                            e.preventDefault();

                            //if shift key is not down, turn off all other .selectedHover items
                            if(!e.shiftKey)
                            {
                                meiEditor.deselectAllHighlights();
                            }


                            if(!$(e.target).hasClass('selectedHover'))
                            {
                                //if this is the first click, find the <neume> object
                                var searchNeedle = new RegExp("<neume.*" + e.target.id, "g");

                                var pageTitle = meiEditor.getActivePanel().text();
                                var testSearch = meiEditorSettings.pageData[pageTitle].find(searchNeedle, 
                                {
                                    wrap: true,
                                    range: null,
                                });

                                //add class and change the background color
                                meiEditor.selectHighlight(e.target);
                            }
                        
                            //don't send to children
                            e.stopPropagation();
                        });
                    };

                    meiEditorSettings.neumeObjects = {};
                    var x2js = new X2JS(); //from xml2json.js
                    meiEditorSettings.divaInstance.resetHighlights();
                    for(curKey in meiEditorSettings.divaImagesToMeiFiles)
                    { //for each page
                        var pageName = meiEditorSettings.divaImagesToMeiFiles[curKey];
                        pageIndex = meiEditorSettings.divaPageList.indexOf(curKey);
                        pageText = meiEditorSettings.pageData[pageName].getSession().doc.getAllLines().join("\n"); //get the information from the page expressed in one string
                        jsonData = x2js.xml_str2json(pageText); //turn this into a JSON "dict"
                        regions = [];

                        xmlns = jsonData['mei']['_xmlns'] //find the xml namespace file
                        var neume_ulx, neume_uly, neume_width, neume_height;
                        neumeArray = jsonData['mei']['music']['body']['neume'];
                        facsArray = jsonData['mei']['music']['facsimile']['surface']['zone'];
                        for (curZoneIndex in facsArray) //for each "zone" object
                        { 
                            curZone = facsArray[curZoneIndex];
                            neumeID = curZone._neume;
                            for (curNeumeIndex in neumeArray) //find the corresponding neume - don't think there's a more elegant way in JS
                            { 
                                if (neumeArray[curNeumeIndex]["_xml:id"] == neumeID)
                                {
                                    curNeume = neumeArray[curNeumeIndex]; //assemble the info on the neume
                                    meiEditorSettings.neumeObjects[neumeID] = curNeume['_name']
                                    neume_ulx = curZone._ulx;
                                    neume_uly = curZone._uly;
                                    neume_width = curZone._lrx - neume_ulx;
                                    neume_height = curZone._lry - neume_uly;
                                    break;
                                }
                            }
                            //add it to regions
                            regions.push({'width': neume_width, 'height': neume_height, 'ulx': neume_ulx, 'uly': neume_uly, 'divID': neumeID});
                        }
                        //at the end of each page, call the highlights
                        meiEditorSettings.divaInstance.highlightOnPage(pageIndex, regions, undefined, "overlay-box", reapplyHoverListener);
                    }
                };


                meiEditor.selectHighlight = function(divToSelect)
                {
                    $(divToSelect).addClass('selectedHover');
                    $(divToSelect).css('background-color', 'background-color:rgba(0, 255, 0, 0.1)');
                }

                meiEditor.deselectAllHighlights = function()
                {
                    $(".selectedHover").css('background-color', 'rgba(255, 0, 0, 0.2)');
                    $(".selectedHover").toggleClass("selectedHover");
                }

                meiEditor.deselectHighlight = function(divToDeselect)
                {
                    $(divToDeselect).css('background-color', 'rgba(255, 0, 0, 0.2)');
                    $(divToDeselect).toggleClass("selectedHover");

                }
                /*
                    Automatically links all MEI files and Diva files by snipping off file extensions and finding matches.
                */

                meiEditor.autoLinkFiles = function()
                {
                    var linkedArr = [];
                    //for each ordered page
                    for(curMei in meiEditorSettings.pageData)
                    {
                        //get the extension; if one doesn't exist, skip this file.
                        if(typeof(curMei.split(".")[1]) == "undefined")
                        {
                            continue;
                        }
                        var meiExtLength = curMei.split(".")[1].length + 1;

                        //for each diva image
                        for(curDivaIndex in meiEditorSettings.divaPageList)
                        {
                            //same
                            var curDivaFile = meiEditorSettings.divaPageList[curDivaIndex];
                            var divaExtLength = curDivaFile.split(".")[1].length + 1;

                            //if the two filenames are equal
                            if(curMei.slice(0, -(meiExtLength)) == curDivaFile.slice(0, -(divaExtLength)))
                            {
                                //grab the option elements that we eventually need to hide by searching for the filename in the parent select object
                                var meiOption = $("#selectfile-link").find(':contains("' + curMei + '")');
                                var imageOption = $("#selectdiva-link").find(':contains("' + curDivaFile + '")')

                                //link 'em, and we found it so break
                                meiEditor.linkMeiToDiva(meiOption, imageOption);
                                linkedArr.push(curMei);
                                break;
                            }
                        }
                    }
                    meiEditor.localLog("Linked " + linkedArr.length + " of " + Object.keys(meiEditorSettings.pageData).length + " total MEI files. (" + linkedArr.join(', ') + ")");
                    meiEditor.createHighlights();
                }

                /*
                    Determines if a mei file is linked to an image.
                    @param meiFile the mei file to check
                */
                meiEditor.meiIsLinked = function(meiFile)
                {
                    for(curDivaFile in meiEditorSettings.divaImagesToMeiFiles)
                    {
                        if(meiFile == meiEditorSettings.divaImagesToMeiFiles[curDivaFile])
                        {
                            return curDivaFile;
                        }
                    }
                    return false;
                }

                /* 
                    Function that links an mei file to a diva image.
                    @param selectedMEI The MEI page to link
                    @param selectedImage The image to link.
                */
                
                meiEditor.linkMeiToDiva = function(selectedMei, selectedImage)
                {
                    //prep variables
                    var selectedMeiText = selectedMei.text();
                    var selectedImageText = selectedImage.text();
                    var selectedStrippedMEI = selectedMeiText.replace(/\W+/g, "");
                    var selectedStrippedImage = selectedImageText.replace(/\W+/g, "");

                    //make the link
                    meiEditorSettings.divaImagesToMeiFiles[selectedImageText] = selectedMeiText;

                    //make the option object
                    $("#selectUnlink").append("<option>" + selectedMeiText + " and " + selectedImageText + "</option>");

                    //byebye
                    $(selectedMei).remove();
                    $(selectedImage).remove();
                }
                /*
                    This is a separate function as it's used in two locations.
                */
                meiEditor.reapplyEditorClickListener = function()
                {
                    $(".aceEditorPane").on('click', function()
                    {
                        var activeTab = meiEditor.getActivePanel().text();
                        if(meiEditor.meiIsLinked(activeTab))
                        {
                            var row = meiEditorSettings.pageData[activeTab].getCursorPosition().row;
                            var rowText = meiEditorSettings.pageData[activeTab].session.doc.getLine(row);
                            var matchArr = rowText.match(/m-[(0-9|a-f)]{8}(-[(0-9|a-f)]{4}){3}-[(0-9|a-f)]{12}/g);
                            var curMatch = matchArr.length;
                            while(curMatch--)
                            {
                                if($("#"+matchArr[curMatch]).length)
                                {
                                    meiEditor.selectHighlight($("#"+matchArr[curMatch]));
                                }
                            }
                        }
                    });
                }

                $.ajax( //this grabs the json file to get an meiEditor-local list of the image filepaths
                {
                    url: meiEditorSettings.jsonFileLocation,
                    cache: true,
                    dataType: 'json',
                    success: function (data, status, jqxhr)
                    {
                        for(curPage in data.pgs)
                        {
                            fileNameOriginal = data.pgs[curPage].f; //original file name
                            fileNameStripped = fileNameOriginal.replace(/\W+/g, ""); //used for jQuery selectors as they can't handle periods easily
                            meiEditorSettings.divaPageList.push(fileNameOriginal);
                            $("#selectdiva-link").append("<option name='"+fileNameOriginal+"'>" + fileNameOriginal + "</option>");
                        }
                    }
                });

                //when the page changes, make the editor reflect that
                diva.Events.subscribe("VisiblePageDidChange", function(pageNumber, fileName)
                {
                    //only if it's linked
                    if(fileName in meiEditorSettings.divaImagesToMeiFiles)
                    {
                        var activeFileName = meiEditorSettings.divaImagesToMeiFiles[fileName];
                        var tabArr = $("#pagesList > li > a");
                        for(curTabIndex in tabArr)
                        {
                            var curTab = tabArr[curTabIndex];
                            if($(curTab).text() == activeFileName)
                            {
                                $("#openPages").tabs("option", "active", curTabIndex);
                                return;
                            }
                        }
                    }
                });

                meiEditor.events.subscribe("NewFile", function(a, fileName)
                {
                    $("#selectfile-link").append("<option name='" + fileName + "'>" + fileName + "</option>");
                    meiEditor.reapplyEditorClickListener();
                });

                meiEditor.events.subscribe("PageEdited", meiEditor.createHighlights);

                meiEditor.events.subscribe("PageWasDeleted", function(pageName)
                {
                    var retVal = meiEditor.meiIsLinked(pageName);
                    if(retVal)
                    {
                        delete meiEditorSettings.divaImagesToMeiFiles[retVal];
                    }
                });
                //to get default pages
                meiEditor.reapplyEditorClickListener();

                //when "Link selected files" is clicked
                $("#link-files").on('click', function()
                {
                    //grab the IDs/stripped IDs of the linked files
                    var selectedMEI = $('#selectfile-link').find(':selected');
                    var selectedImage = $('#selectdiva-link').find(':selected');

                    //if there's not 2 selected files, "throw" an error
                    if(selectedMEI === undefined || selectedImage === undefined)
                    {
                        meiEditor.localLog("Please make sure that an MEI file and an image are selected.");
                        return;
                    } 
                    else 
                    {
                        meiEditor.localLog("Successfully linked " + selectedMEI.text() + " to " + selectedImage.text() + ".");
                    }

                    meiEditor.linkMeiToDiva(selectedMEI, selectedImage);

                    //because one line of code helps prevent one pound of laziness; this is here so that autoLink doesn't call it
                    meiEditor.createHighlights();
                });

                $("#unlink-files").on('click', function()
                {
                    var selectedPair = $('#selectUnlink').find(':selected');
                    var fileArr = selectedPair.text().split(' and ');

                    //change the data/DOM
                    delete meiEditorSettings.divaImagesToMeiFiles[fileArr[1]];
                    $("#selectfile-link").append("<option name='" + fileArr[0] + "'>" + fileArr[0] + "</option>");
                    $("#selectdiva-link").append("<option name='" + fileArr[1] + "'>" + fileArr[1] + "</option>");
                    $(selectedPair).remove();

                    meiEditor.localLog("Successfully unlinked " + fileArr[0] + " from " + fileArr[1] + ".");

                    //reload highlights
                    meiEditor.createHighlights();

                });

                //delete listener for selected overlay-boxes
                $(document).on('keyup', function(e)
                {
                    if(e.keyCode == 46) //delete, as backspace triggers a history.back event
                    {
                        e.preventDefault();

                        //remove the highlight object and the reference from the neumeObjects array
                        var saveObject = [];
                        var curItemIndex = $(".selectedHover").length;
                        while(curItemIndex--)
                        {
                            var curItem = $(".selectedHover")[curItemIndex];    
                            var itemID = $(curItem).attr('id');
                            
                            /* //remove item from display, remove from neumeObjects
                            $(curItem).remove();
                            delete meiEditorSettings.neumeObjects[itemID]; */


                            //perform a new search to grab all occurences of the id and to delete both lines
                            var pageTitle = meiEditor.getActivePanel().text();
                            var uuidSearch = meiEditorSettings.pageData[pageTitle].findAll(itemID, 
                            {
                                wrap: true,
                                range: null,
                            });

                            //this may not be the right way to do it, but "findAll" returns how many it found, and there doesn't seem to be a clear way to select everything at once. This accurately deletes all instances, however.
                            while(uuidSearch)
                            {
                                var row = meiEditorSettings.pageData[pageTitle].getSelectionRange().start.row;
                                var text = meiEditorSettings.pageData[pageTitle].session.doc.getLine(row);
                                saveObject.push({'doc': pageTitle, 'row': row, 'text': text});

                                meiEditorSettings.pageData[pageTitle].removeLines();
                                uuidSearch = meiEditorSettings.pageData[pageTitle].findAll(itemID, 
                                {
                                    wrap: true,
                                    range: null,
                                });
                            }
                            
                            //meiEditorSettings.undoManager.save('deletion', saveObject); do need a separate one here so I can call createhighlights

                        }
                        meiEditor.createHighlights();
                        meiEditor.localLog("Deleted a highlight.");                                
                    }
                });

                $(document).on('keydown', function(e)
                {
                    if(e.shiftKey)
                    {
                        $(document).on('keyup', function(e)
                        {
                            if(!e.shiftKey)
                            {
                                $("#cover-div").remove();
                            }
                        });

                        //if user is holding shift, append a div on top of everything that covers diva-wrapper (and thus negates its click/drag binding)
                        $("#topbar").append('<div id="cover-div"></div>')
                        $("#cover-div").height($("#diva-wrapper").height());
                        $("#cover-div").width($("#diva-wrapper").width());
                        $("#cover-div").offset({'top': 0, 'left': $("#diva-wrapper").offset().left});

                        //hover-div listener
                        $("#cover-div").on('mousemove', function(e)
                        {
                            //if hoverdiv currently exists
                            if(!($("#hover-div").css('display') == "none"))
                            {
                                var curOverlay = meiEditorSettings.curOverlayBox;
                                var outsideCheck = false;
                                //if it's outside, trigger mouseleave
                                if(e.pageX < curOverlay.offset().left)
                                    curOverlay.trigger('mouseleave');
                                else if(e.pageX > (curOverlay.offset().left + curOverlay.width()))
                                    curOverlay.trigger('mouseleave');
                                else if(e.pageY < curOverlay.offset().top)
                                    curOverlay.trigger('mouseleave');
                                else if(e.pageY > (curOverlay.offset().top + curOverlay.height()))
                                    curOverlay.trigger('mouseleave');
                            }
                            else 
                            {
                                //for each overlaybox
                                var curBoxIndex = $(".overlay-box").length;
                                while(curBoxIndex--)
                                {
                                    //if the mouse is inside
                                    var curOverlay = $($(".overlay-box")[curBoxIndex]);
                                    if(e.pageX < curOverlay.offset().left)
                                        continue;
                                    if(e.pageX > (curOverlay.offset().left + curOverlay.width()))
                                        continue;
                                    if(e.pageY < curOverlay.offset().top)
                                        continue;
                                    if(e.pageY > (curOverlay.offset().top + curOverlay.height()))
                                        continue;

                                    //trigger
                                    meiEditorSettings.curOverlayBox = curOverlay; //save time turning off
                                    curOverlay.trigger('mouseenter');

                                    //can only happen once, so let's save ourselves some time
                                    break;
                                }
                            }
                        });

                        //when you click on that div
                        $("#cover-div").on('mousedown', function(e)
                        {
                            e.preventDefault();

                            //append the div that will resize as you drag
                            $("#topbar").append('<div id="drag-div"></div>');
                            meiEditorSettings.initDragTop = e.pageY;
                            meiEditorSettings.initDragLeft = e.pageX;
                            $("#drag-div").offset({'top': e.pageY, 'left':e.pageX})

                            //as you drag, resize it 
                            $(document).on('mousemove', function(ev)
                            {
                                //original four sides
                                var dragLeft = $("#drag-div").offset().left;
                                var dragTop = $("#drag-div").offset().top;
                                var dragRight = dragLeft + $("#drag-div").width();
                                var dragBottom = dragTop + $("#drag-div").height();           

                                //if we're moving left
                                if(ev.pageX < meiEditorSettings.initDragLeft)
                                {
                                    $("#drag-div").offset({'left': ev.pageX});
                                    $("#drag-div").width(dragRight - ev.pageX);
                                }
                                //moving right
                                else 
                                {   
                                    $("#drag-div").width(ev.pageX - dragLeft);
                                }
                                //moving up
                                if(ev.pageY < meiEditorSettings.initDragTop)
                                {
                                    $("#drag-div").offset({'top': ev.pageY});
                                    $("#drag-div").height(dragBottom - ev.pageY);
                                }
                                //moving down
                                else 
                                {
                                    $("#drag-div").height(ev.pageY - dragTop);
                                }
                            });

                            //when you let go of the mouse
                            $(document).on('mouseup', function(eve){
                                $(document).unbind('mousemove');
                                $(document).unbind('mouseup');


                                //there's gotta be something simpler than this, but I can't find it for the life of me.
                                //get the four sides
                                var boxLeft = $("#drag-div").offset().left;
                                var boxRight = boxLeft + $("#drag-div").width();
                                var boxTop = $("#drag-div").offset().top;
                                var boxBottom = boxTop + $("#drag-div").height();

                                //for each overlay-box
                                var curBoxIndex = $(".overlay-box").length;
                                while(curBoxIndex--)
                                {
                                    var curBox = $(".overlay-box")[curBoxIndex];

                                    //see if any part of the box is inside (doesn't have to be the entire box)
                                    var curLeft = $(curBox).offset().left;
                                    var curRight = curLeft + $(curBox).width();
                                    var curTop = $(curBox).offset().top;
                                    var curBottom = curTop + $(curBox).height();
                                    if(curRight < boxLeft)
                                        continue
                                    else if(curLeft > boxRight)
                                        continue
                                    else if(curBottom < boxTop)
                                        continue
                                    else if(curTop > boxBottom)
                                        continue
                
                                    //if we're still here, select it
                                    $(curBox).addClass('selectedHover');
                                    $(curBox).css('background-color', 'background-color:rgba(0, 255, 0, 0.2)');
                                }

                                //remove the resizing div
                                $("#drag-div").remove();
                            });
                            e.stopPropagation();
                        });
                    }
                });

                return true;
            }
        }
        return retval;
    })());
    window.pluginLoader.pluginLoaded();
})(jQuery);

});