var meiEditorFileUpload = function()
{
	var retval = 
	{
		divName: "file-upload",
	    maximizedAppearance: '<input type="file" value="Add a new file" id="fileInput">' 
	        +'<div id="file-list">Files loaded:<br></div>'
	        +'<button id="updateDiva">Update DIVA</button>'
	        +'<button class="minimize" name="file-upload" style="float:right;">Minimize</button>',
    	minimizedAppearance: '<span>Files loaded:</span>'
        	+'<button class="maximize" name="file-upload" style="float:right;">Maximize</button>',
	    _init: function(meiEditor, meiEditorSettings){
	    	$.extend(meiEditorSettings, {
	    		activeDoc: "",
	    		currentPage: "",
	            currentDocPosition: {'row': 1, 'col': 1},
	            pageData: {},
	            orderedPageData: [],
	            neumeObjects: [],
	            currentTarget: "",
	    	});
	        /*
	            Changes the active page in the editor.
	            @param pageName The page to switch to.
	        */
	        meiEditor.changeActivePage = function(pageName)
	        {
	            meiEditorSettings.editor.setSession(pageData[pageName]); //inserts text
	            meiEditorSettings.activeDoc = editor.getSession().doc;
	        };

	        /*
	            Prompts local download of a page.
	            @param pageName The page to download.
	        */
	        meiEditor.savePageToClient = function(pageName)
	        {
	            formatToSave = function(lineIn, indexIn)
	            {          
	                if(lineIn !== "") //if the line's not blank (nothing in MEI should be)
	                {
	                    formattedData[indexIn] = lineIn + "\n"; //add a newline - it doesn't use them otherwise. Last line will have a newline but this won't stack when pages are re-uploaded as this also removes blank lines.
	                }
	            }

	            var formattedData = [];
	            var lastRow = pageData[pageName].doc.getLength() - 1; //0-indexed
	            pageData[pageName].doc.getLines(0, lastRow).forEach(formatToSave); //format each
	            var pageBlob = new Blob(formattedData, {type: "text/plain;charset=utf-8"}); //create a blob
	            saveAs(pageBlob, pageName); //download it! from FileSaver.js
	        };
		    /*
	            Adds a page to the database
	            @param pageDataIn The result of a FileReader.readAsText operation containing the data from the MEI file.
	            @param fileNameIn The name of the file to be referenced in the database.
	        */
	        meiEditor.addPage = function(pageDataIn, fileNameIn)
	        {
	            meiEditorSettings.pageData[fileNameIn] = new ace.EditSession(pageDataIn, "ace/mode/xml"); //add the file's data into a "pageData" array that will eventually feed into the ACE editor
	            meiEditorSettings.orderedPageData.push(fileNameIn); //keep track of the page orders to push the right highlights to the right pages
	        };
		    /* 
	            Validates MEI using the locally-hosted .RNG file
	            @param pageName The page to validate.
	        */
	        meiEditor.validateMei = function(pageName)
	        {
	            var Module = 
	            {
	                xml: pageData[pageName].doc.getAllLines().join("\n"),
	                schema: validatorText,
	                //arguments: ["--noout", "--relaxng", "http://localhost:8000/mei-Neumes.rng", "http://localhost:8000/mei/015.xml"]
	            }
	            validationWorker = new Worker("xmllintNew.js");
	            validationWorker.onmessage = function(event){
	                console.log(event.data);
	            }
	            validationWorker.postMessage(Module);
	        }
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

		                $("#hover-div").html(neumeObjects[currentTarget]);
		                $("#hover-div").css(//create a div with the name of the hovered neume
		                {
		                    'top': e.pageY - 50,
		                    'height': 40,
		                    'left': e.pageX,
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
		                    $("#hover-div").css(
		                    {
		                        'top': e.pageY - 50,
		                        'left': e.pageX,
		                    });
		                });
		            }, function(e){
		                currentTarget = e.target.id;
		                $(document).unbind('mousemove'); //stops moving the div
		                $("#hover-div").css('display', 'none'); //hides the div
		                $("#hover-div").html("");

		                $("#"+currentTarget).css('background-color', 'rgba(255, 0, 0, 0.2)'); //color is normal again
		            });
		        };

	            var x2js = new X2JS(); //from xml2json.js
	            var pageIndex = orderedPageData.length;
	            dv.resetHighlights();
	            while(pageIndex--)
	            { //for each page
	                curPage = orderedPageData[pageIndex];
	                pageText = pageData[curPage].doc.getAllLines().join("\n"); //get the information from the page expressed in one string
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
	                            neumeObjects[neumeID] = curNeume['_name']
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
	                dv.highlightOnPage(pageIndex, regions, undefined, "overlay-box", reapplyHoverListener);
	            }
	        };



	        $("#updateDiva").on('click', meiEditor.createHighlights);

	        //when a new file is uploaded; easier to write inline than separately because of the "this" references
            $('#fileInput').change(function(e)
            { 
                var reader = new FileReader();
                reader.file = this.files[0];

                //when the file is loaded as text
                reader.onload = function(e) 
                { 
                    fileName = this.file.name
                    meiEditor.addPage(this.result, fileName);
                    $("#file-list").html($("#file-list").html()
                        +"<div class='meiFile' id='"+fileName+"'>"+fileName
                        +"<button class='meiLoad' pageTitle='"+fileName+"'>Load</button>"
                        +"<button class='meiSave' pageTitle='"+fileName+"'>Save</button>"
                        +"</div>"); //add the file to the GUI
                   	if(typeof(meiEditorXMLValidator) !== undefined){
	                    $("#validate-file-list").html($("#validate-file-list").html()
	                        +"<div class='meiFile' id='"+fileName+"'>"+fileName
	                        +"<button class='meiValidate' pageTitle='"+fileName+"'>Validate</button>"
	                        +"</div>"); //add the file to the GUI
                   	}
                    meiEditor.reapplyButtonListeners();
                };
                reader.readAsText(this.files[0]);
            });

            //various jQueryUI designators
            $("#file-list").sortable();
            $("#file-list").disableSelection();
            $("#file-list").on("sortstop", function(e, ui) //when dragging a sortable item ends
            {
		        /*
		            Reorders the MEI files in the data to reflect the GUI.
		            @param newOrder A list of the filenames in the desired order.
		        */
		        var reorderFiles = function(newOrder)
		        {
		            orderedPageData = [];
		            var curPage = 0;
		            while(curPage < newOrder.length) //go through new order 
		            {
		                orderedPageData.push(newOrder[curPage]); //push them into ordered array
		                curPage++;
		            }
		        };
                fileList = $(".meiFile"); //gets a list of all objects with the "meiFile" class
                newOrder = [];
                numberOfFiles = $(".meiFile").length;
                for(curFileIndex = 0; curFileIndex < numberOfFiles; curFileIndex++)
                {
                    newOrder.push(fileList[curFileIndex].id); //creates an array with the new order
                }
                reorderFiles(newOrder);
            });
	    }
	}
	return retval;
}