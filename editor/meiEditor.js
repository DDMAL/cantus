var AceMeiEditor = function(aceEditor){
    var activeDoc = aceEditor.getSession().doc;
    var currentPage;
    var currentDocPosition = {'row': 1, 'col': 1};
    var pageData = {};
    var orderedPageData = [];
    var neumeObjects = [];
    var currentTarget;

    this.createHighlights = function()
	{
		function reapplyHoverListener()
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

    this.reorderFiles = function(newOrder){
    	pageData
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

}
