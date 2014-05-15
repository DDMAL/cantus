/*
Small plugin to turn MEI zones into Diva.JS highlighted objects.
Requires:
	-jQuery
	-xml2json.js, can be found at https://x2js.googlecode.com/hg/xml2json.js
Usage:
	-Read a selection of MEI files using the JavaScript FileReader object's readAsText() method
		(new FileReader()).readAsText(files[0])
	-Pass these MEI files into createHighlights()
*/

var neumeObjects = [];
var currentTarget;

/*
    Creates highlight regions from MEI text.
    @param meiArray Array of mei files in raw text
*/
function createHighlights(meiArray)
{
	var x2js = new X2JS(); //from xml2json.js
	var pageIndex = meiArray.length;
	while (pageIndex--)
	{ //for each page
		jsonData = x2js.xml_str2json(meiArray[pageIndex]); //convert to json
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
/*
	Function to be called when everytime the highlights are regenerated to regenerate the on-hover effect
*/
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