var AceMeiEditor = function(){
	var meiArray = [];
    var activeDoc;
    var currentPage;
    var currentDocPosition = {'row': 1, 'col': 1};
    var pageData = {};
    var pageLocToData = {};

	_init = function()
	{
        activeDoc = editor.getSession().doc; //get a reference to the active Document
    }

    this.changeActivePage = function(pageName)
    {
    	editor.setSession(pageData[pageName]); //inserts text
        activeDoc = editor.getSession().doc;
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
    	var tempIndex = meiArray.push(pageDataIn) - 1;
        pageData[fileNameIn] = new ace.EditSession(pageDataIn, "ace/mode/xml"); //add the file's data into a "pageData" array that will eventually feed into the ACE editor
        pageLocToData[fileNameIn] = tempIndex; //because I have to keep the meiArray sequential, populate it into an array that transfers page titles into meiArray sequence
    }

	this.reloadFromACE = function()
    {
        meiArray[pageLocToData[currentPage]] = activeDoc.getAllLines().join("\n"); //
        createHighlights(meiArray);
    }

    this.getMeiArray = function(){
    	return meiArray;
    }

    _init();
}
