var meiEditorXMLValidator = function(){
	var retval = {
		divName: "xml-validator",
	    maximizedAppearance: '<div id="validate-file-list">Files to validate:<br></div>'
        +'<button id="updateDiva">Update DIVA</button>'
        +'<button class="minimize" name="xml-validator" style="float:right;">Minimize</button>',
    	minimizedAppearance: '<span>Files to validate:</span>'
        +'<button class="maximize" name="xml-validator" style="float:right;">Maximize</button>',
	    _init: function(meiEditor, meiEditorSettings){

	    }
	}
	return retval;
}