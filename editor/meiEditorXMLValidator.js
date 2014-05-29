var meiEditorXMLValidator = function(){
	var retval = {
		divName: "xml-validator",
	    maximizedAppearance: '<div id="validate-file-list">Files to validate:<br></div>'
        +'<button class="minimize" name="xml-validator">Minimize</button>',
    	minimizedAppearance: '<span>Files to validate:</span>'
        +'<button class="maximize" name="xml-validator">Maximize</button>',
	    _init: function(meiEditor, meiEditorSettings){
	    	/* 
	            Validates MEI using the locally-hosted .RNG file
	            @param pageName The page to validate.
	        */
	        meiEditor.validateMei = function(pageName)
	        {
	            var Module = 
	            {
	                xml: meiEditorSettings.pageData[pageName].doc.getAllLines().join("\n"),
	                schema: meiEditorSettings.validatorText,
	            }
	            validationWorker = new Worker("xmllintNew.js");
	            validationWorker.pageName = pageName;
	            validationWorker.onmessage = function(event)
	            {
	            	pageName = this.pageName;
	            	console.log(pageName, event.data, $("#validate-output-"+pageName));
	                $("#validate-output-" + pageName).html($("#validate-output-" + pageName).html() + "<br>" + event.data);
	            }
	            validationWorker.postMessage(Module);
	        }

	        //load in the XML validator

            $.ajax(
            {
                url: meiEditorSettings.validatorLink,
                success: function(data)
                {
                    meiEditorSettings.validatorText = data;
                }
            });

            $("#" + this.divName).on('maximize', function(){
            	console.log("I just got maximized!");
            })
	    }
	}
	return retval;
}