/*
Small plugin to turn MEI zones into Diva.JS highlighted objects.
Requires:
	-jQuery
	-xml2json.js, can be found at https://x2js.googlecode.com/hg/xml2json.js
Usage:
	-Read a selection of MEI files using the JavaScript FileReader object's readAsText() method
		(new FileReader()).readAsText(files[0])
*/

var neumeObjects = [];
var currentTarget;

function createHighlights(meiArray){
	var x2js = new X2JS(); //from plugin
	for(var pageIndex = 0; pageIndex < meiArray.length; pageIndex++)
	{
		jsonData = x2js.xml_str2json(meiArray[pageIndex]);
		regions = [];

		xmlns = jsonData['mei']['_xmlns']
		var neume_ulx, neume_uly, neume_width, neume_height;
		neumeArray = jsonData['mei']['music']['body']['neume'];
		facsArray = jsonData['mei']['music']['facsimile']['surface']['zone'];

		for(curZoneIndex in facsArray)
		{
			curZone = facsArray[curZoneIndex];
			neumeID = curZone._neume;
			for(curNeumeIndex in neumeArray)
			{
				if (neumeArray[curNeumeIndex]["_xml:id"] == neumeID)
				{
					curNeume = neumeArray[curNeumeIndex];
					neumeObjects[neumeID] = curNeume['_name']
					neume_ulx = curZone._ulx;
					neume_uly = curZone._uly;
					neume_width = curZone._lrx - neume_ulx;
					neume_height = curZone._lry - neume_uly;
					break;
				}
			}
			regions.push({'width': neume_width, 'height': neume_height, 'ulx': neume_ulx, 'uly': neume_uly, 'divID': neumeID});
		}
		dv.highlightOnPage(pageIndex, regions, undefined, "overlay-box", reapplyHoverListener);
	}
}

function reapplyHoverListener(){
	$(".overlay-box").hover(function(e)
	{
		currentTarget = e.target.id;

		$("#hover-div").html(neumeObjects[currentTarget]);
		$("#hover-div").css(
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
		$("#"+currentTarget).css('background-color', 'rgba(255, 255, 255, 0.2)');

		$(document).on('mousemove', function(e)
		{
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

		$("#"+currentTarget).css('background-color', 'rgba(255, 0, 0, 0.5)');
		$("#hover-div").html("");
	});
}