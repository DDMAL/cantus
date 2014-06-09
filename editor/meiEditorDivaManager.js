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
            },
            init: function(meiEditor, meiEditorSettings)
            {
                $.extend(meiEditorSettings, 
                {
                    divaPageList: [], //list of active pages in Diva
                    divaImagesToMeiFiles: {}, //keeps track of linked files
                    neumeObjects: {}
                });

                $("#file-link-dropdown").on('click', function(){
                    $('#fileLinkModal').modal();
                });

                $("#file-unlink-dropdown").on('click', function(){
                    $('#fileUnlinkModal').modal();
                });

                $("#auto-link-dropdown").on('click', function(){
                    meiEditor.autoLinkFiles();
                });

                $("#update-diva-dropdown").on('click', function(){
                    meiEditor.createHighlights();
                })

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
                            //change the color of the hovered div
                            $("#"+currentTarget).css('background-color', 'rgba(255, 255, 255, 0.05)');

                            $(document).on('mousemove', function(e) //have it follow the mouse
                            {
                                $("#hover-div").offset(
                                {
                                    'top': e.pageY - 10,
                                    'left': e.pageX + 10,
                                });
                            });
                        }, function(e){
                            currentTarget = e.target.id;
                            $(document).unbind('mousemove'); //stops moving the div
                            $("#hover-div").css('display', 'none'); //hides the div
                            $("#hover-div").html("");

                            $("#"+currentTarget).css('background-color', 'rgba(255, 0, 0, 0.2)'); //color is normal again
                        });
                        $(".overlay-box").click(function(e)
                        {
                            var pageTitle = meiEditor.getActivePanel().text();
                            var searchNeedle = new RegExp("<neume.*" + e.target.id, "g");
                            var testSearch = meiEditorSettings.pageData[pageTitle].find(searchNeedle, 
                            {
                                wrap: true,
                                range: null,
                            });
                            console.log(testSearch);
                        });
                    };

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
                    //if they're linked, change them
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
                });


                //when "Link selected files" is clicked
                $("#link-files").on('click', function(){
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
                });

                $("#unlink-files").on('click', function(){
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

                return true;
            }
        }
        return retval;
    })());
})(jQuery);