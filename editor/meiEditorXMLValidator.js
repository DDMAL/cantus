var meiEditorXMLValidator = function(){
    var retval = {
        divName: "xml-validator",
        minimizedTitle: "Files to validate:",
        maximizedAppearance: 'Files to validate:<br><div id="validate-file-list"></div>',
        minimizedAppearance: '<span id="numNewMessages">0</span>',
        _init: function(meiEditor, meiEditorSettings){
            $.extend(meiEditorSettings, {
                validatorLink: "mei-Neumes.rng",
                validatorText: "",
            });
            /* 
                Function called to reapply button listeners
            */
            var reapplyXMLValidatorButtonListeners = function(){
                $(".meiClear").on('click', function(e)
                {
                    fileName = $(e.target).attr('pageTitle'); //grabs page title from custom attribute
                    $("#validate-output-" + fileName).html("");
                });
                $(".meiValidate").on('click', function(e)
                {
                    fileName = $(e.target).attr('pageTitle'); //grabs page title from custom attribute
                    meiEditor.validateMei(fileName, fileNameOriginal);
                });
            }
            
            /* 
                Validates MEI using the locally-hosted .RNG file
                @param pageName The page to validate.
            */
            meiEditor.validateMei = function(pageName, pageNameOriginal)
            {
                var Module = 
                {
                    xml: meiEditorSettings.pageData[pageName].doc.getAllLines().join("\n"),
                    schema: meiEditorSettings.validatorText,
                    title: pageNameOriginal
                }
                validationWorker = new Worker("xmllintNew.js");
                validationWorker.pageName = pageName;
                $("#validate-output-" + pageName).html("Sent to validator...");
                validationWorker.onmessage = function(event)
                {
                    pageName = this.pageName;
                    $("#validate-output-" + pageName).html($("#validate-output-" + pageName).html() + "<br>" + event.data);
                    if($("#xml-validator").hasClass('minimized')){
                        var curCount = 0;
                        if($("#numNewMessages").html() != ""){
                            curCount = parseInt($("#numNewMessages").html())
                        }
                        curCount += 1;
                        $("#numNewMessages").html(curCount);
                        $("#numNewMessages").css('display', 'block');
                    }
                }
                validationWorker.postMessage(Module);
            }

            meiEditor.events.subscribe("NewFile", function(fileData, fileName, fileNameOriginal){
                $("#validate-file-list").html($("#validate-file-list").html()
                    + "<div class='meiFile' pageTitle='" + fileName + "' id='validate-" + fileName + "'>" + fileNameOriginal
                    + "<span class='meiFileButtons'>"
                    + "<button class='meiClear' pageTitle='" + fileName + "'>Clear output</button>"
                    + "<button class='meiValidate' pageTitle='" + fileName + "' pageTitleOrig='" + fileNameOriginal + "'>Validate</button>"
                    + "</span>"
                    + "<div class='validateOutput' id='validate-output-" + fileName + "'></div>"
                    + "</div>");
                reapplyXMLValidatorButtonListeners();
            });

            meiEditor.events.subscribe("NewOrder", function(newOrder){
                {
                    var tempChildren = [];
                    var curPage = 0;
                    while(curPage < newOrder.length)
                    {
                        var curPageTitle = newOrder[curPage];
                        var curChildren = $("#validate-file-list").children();
                        var curCount = curChildren.length;
                        while(curCount--)
                        {
                            if($(curChildren[curCount]).attr('pageTitle') == curPageTitle)
                            {
                                tempChildren.push(curChildren[curCount].outerHTML);
                                break;
                            } 
                        }
                        curPage++;
                    }
                    $("#validate-file-list").html(tempChildren.join(""));
                }
                reapplyXMLValidatorButtonListeners();
            });

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
                $("#numNewMessages").css('display', 'block');
                $("#numNewMessages").html('0');
            });

            $("#" + this.divName).on('minimize', function(){
                if($("#numNewMessages").html() == '0'){
                    $("#numNewMessages").css('display', 'none');
                }
            });
        }
    }
    return retval;
}