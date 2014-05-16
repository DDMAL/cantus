(function ($)
{
	var AceMeiEditor = function(element, aceEditor){
		var element = $(element);
		var self = this;
	    var activeDoc = aceEditor.getSession().doc;
	    var currentPage;
	    var currentDocPosition = {'row': 1, 'col': 1};
	    var pageData = {};
	    var orderedPageData = [];
	    var neumeObjects = [];
	    var currentTarget;
	    var dv;
	    var editor;

	    var reapplyLoadSaveListeners = function()
	    {
	    	$(".meiLoad").on('click', function(e)
	    	{
				fileName = e.target.id.substring(4); //clips off "load" word from ID, there's probably a more graceful way
				self.changeActivePage(fileName);
			});

			$(".meiSave").on('click', function()
			{
				fileName = e.target.id.substring(4); //clips off "save" word from ID
				self.savePageToClient(fileName);
			});
	    }

	    var reapplyHoverListener = function()
	    {
	    	$(".overlay-box").hover(function(e)
			{
				currentTarget = e.target.id;

				$("#hover-div").html(neumeObjects[currentTarget]);
				$("#hover-div").css(
				{//create a div with the name of the hovered neume
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

				$(document).on('mousemove', function(e)
				{//have it follow the mouse
					$("#hover-div").css(
					{
						'top': e.pageY - 50,
						'left': e.pageX,
					});
				});
			}, function(e){
				currentTarget = e.target.id;
				$(document).unbind('mousemove');
				$("#hover-div").css('display', 'none');

				$("#"+currentTarget).css('background-color', 'rgba(255, 0, 0, 0.2)');
				$("#hover-div").html("");
			});
	    }

	    this.createHighlights = function()
		{			
			var x2js = new X2JS(); //from xml2json.js
			var pageIndex = orderedPageData.length;
			while(pageIndex--)
			{ //for each page
				curPage = orderedPageData[pageIndex];
				jsonData = x2js.xml_str2json(pageData[curPage].doc.getAllLines().join("\n"));
				regions = [];

				xmlns = jsonData['mei']['_xmlns'] //find the xml namespace file
				var neume_ulx, neume_uly, neume_width, neume_height;
				neumeArray = jsonData['mei']['music']['body']['neume'];
				facsArray = jsonData['mei']['music']['facsimile']['surface']['zone'];

				for (curZoneIndex in facsArray)
				{ //for each "zone" object
					curZone = facsArray[curZoneIndex];
					neumeID = curZone._neume;
					for (curNeumeIndex in neumeArray)
					{ //find the corresponding neume - don't think there's a more elegant way in JS
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
		}

	    this.changeActivePage = function(pageName)
	    {
	    	editor.setSession(pageData[pageName]); //inserts text
	        activeDoc = editor.getSession().doc;
	    }

	    this.reorderFiles = function(newOrder)
	    {
	    	var curPage = 0;
	    	while(curPage < newOrder.length){
	    		orderedPageData.push(newOrder[curPage]);
	    		curPage++;
	    	}
	    }

	    this.savePageToClient = function(pageName)
	    {
	    	formatToSave = function(lineIn, indexIn)
	    	{          
	        	if(lineIn !== "")
	    		{
	        		formattedData[indexIn] = lineIn + "\n";
	        	}
	    	}

	        var formattedData = [];
	        var lastRow = pageData[pageName].doc.getLength() - 1; //no row 0, rest are 0-index though?
	        pageData[pageName].doc.getLines(0, lastRow).forEach(formatToSave);
	        formattedData[formattedData.length - 1].trim()
	        var pageBlob = new Blob(formattedData, {type: "text/plain;charset=utf-8"});
	        saveAs(pageBlob, pageName);
		  
	    }	

	    this.addPage = function(pageDataIn, fileNameIn)
	    {
	        pageData[fileNameIn] = new ace.EditSession(pageDataIn, "ace/mode/xml"); //add the file's data into a "pageData" array that will eventually feed into the ACE editor
	        orderedPageData.push(fileNameIn); //keep track of the page orders to push the right highlights to the right pages
	    }

	    var _init = function()
	    {

	    	element.append('<div id="editor"></div>'
    			+'<div id="diva-wrapper"></div>'
    			+'<div class="clear"></div>'
    			+'<div id="mei-editor"></div>'
    			+'<span id="hover-div"></span><div id="file-upload">'
        		+'<div id="file-upload-contents-wrapper">'
            	+'<input type="file" value="Add a new file" id="fileInput">'
            	+'<div id="file-list">Files loaded:<br></div>'
            	+'<button id="updateDiva">Update DIVA</button>'
            	+'<button id="minimize" style="float:right;">Minimize</button>'
        		+'</div>'
        		+'<div id="file-upload-minimized-wrapper" style="display:none;">'
            	+'<span id="file-list">Files loaded:</span>'
            	+'<button id="maximize" style="float:right;">Maximize</button>'
        		+'</div>'
    			+'</div>');
	    	$('#diva-wrapper').diva(
	        {//create the diva wrapper
	            contained: true,
	            enableAutoHeight: true,
	            fixedHeightGrid: false,
	            iipServerURL: "http://132.206.14.136:8000/fcgi-bin/iipsrv.fcgi",
	            objectData: "imagesOut.json",
	            imageDir: "/opt/stgall",
	            enableHighlight: true
	        });
	        dv = $('#diva-wrapper').data('diva');
	        editor = ace.edit("editor"); //create the ACE editor
	        editor.setTheme("ace/theme/ambiance");
	        editor.getSession().setMode("ace/mode/xml");

	    	$("#updateDiva").on('click', self.createHighlights);

	    	$("#minimize").on('click', function(){
	    		previousWidth = $("#file-upload").width();
	            $("#file-upload-minimized-wrapper").css('display', 'block');
	            $("#file-upload-contents-wrapper").css('display', 'none');
	            $("#file-upload").width(previousWidth);
	    	});

	    	$("#maximize").on('click', function(){
	    		$("#file-upload-contents-wrapper").css('display', 'block');
	            $("#file-upload-minimized-wrapper").css('display', 'none');
	        });

	        $('#fileInput').change(function(e)
	        { 
	            var reader = new FileReader();
	            reader.file = this.files[0];

	            //when the file is loaded as text
	            reader.onload = function(e) 
	            { 
	                fileName = this.file.name
	                self.addPage(this.result, fileName);
	                //$("#file-list").html($("#file-list").html()+"<span class='meiFile'><span class='meiName'>"+this.file.name+"</span><span class='meiLoad' onclick='loadPage(\""+this.file.name+"\")'>Load</span><span class='meiSave' onclick='savePage(\""+this.file.name+"\")'>Save</span></span>"); //add the file to the GUI    
	                $("#file-list").html($("#file-list").html()
	                	+"<div class='meiFile' id='"+fileName+"'>"+fileName
	                	+"<button class='meiLoad' id='load"+fileName+"'>Load</button>"
	                	+"<button class='meiSave' id='save"+fileName+"'>Save</button>"
	                	+"</div>"); //add the file to the GUI
	                reapplyLoadSaveListeners();
	            };
	            reader.readAsText(this.files[0]);
	        });

        	//various jQueryUI designators
	        $("#file-upload").draggable();
	        $("#file-list").sortable();
	        $("#file-list").disableSelection();
	        $("#file-list").on("sortstop", function(e, ui){
	            fileList = $(".meiFile");
	            newOrder = [];
	            numberOfFiles = $(".meiFile").length;
	            for(curFileIndex = 0; curFileIndex < numberOfFiles; curFileIndex++)
	            {
	                newOrder.push(fileList[curFileIndex].id);
	            }
	            meiEditor.reorderFiles(newOrder);
	        });
	    }    

	    _init();

	}

    $.fn.AceMeiEditor = function (options)
    {
        return this.each(function ()
        {
            var element = $(this);

            // Return early if this element already has a plugin instance
            if (element.data('AceMeiEditor'))
                return;

            // Save the reference to the container element
            options.parentSelector = element;

            // Otherwise, instantiate the document viewer
            var meiEditor = new AceMeiEditor(this, options);
            element.data('AceMeiEditor', meiEditor);
        });
    };

})(jQuery);