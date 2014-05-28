(function ($)
{
    var AceMeiEditor = function(element, plugins, options){
        var element = $(element);
        var self = this;
        var settings = {
            dv: "",
            editor: "",
            validatorLink: "mei-Neumes.rng",
            validatorText: "",
        }

        //for topbar plugins
        var numMinimized = 0;
        var previousSizes = {};

        /*
            Function called when new load/save buttons are created to refresh the listeners.
        */
        this.reapplyButtonListeners = function()
        {
            $(".meiLoad").on('click', function(e)
            {
                fileName = $(e.target).attr('pageTitle'); //grabs page title from custom attribute
                self.changeActivePage(fileName);
            });

            $(".meiSave").on('click', function(e)
            {
                fileName = $(e.target).attr('pageTitle'); //grabs page title from custom attribute
                self.savePageToClient(fileName);
            });

            $(".meiValidate").on('click', function(e)
            {
                fileName = $(e.target).attr('pageTitle'); //grabs page title from custom attribute
                self.validateMei(fileName);
            });
        };

        /*
            Minimizes an object.
            @param divID The root ID of the object to minimize.
            @param animateOverride Used at initial load and as needed after to override the animation to old position.
        */
        var minimizeObject = function(divID, animateOverride){
            if(typeof animateOverride === undefined){
                animateOverride = false;
            }
            //previousWidth = $("#file-upload").width(); //needed to make it look nice. could take this out.
            previousSizes[divID] = 
            {
                 'left': $("#"+divID).offset().left,
                 'top': $("#"+divID).offset().top,
                 'width': $("#"+divID).width(),
                 'height': $("#"+divID).height(),
                 'margin': $("#"+divID).css('margin'),
                 'padding': $("#"+divID).css('padding'),
            };

            if(!animateOverride){
                $("#"+divID).animate(
                {
                    'left': numMinimized*200,
                    'margin': '2px',
                    'width': '196px',
                    'height': 'auto',
                    'top': '0px',
                    'padding': '3px',
                }, 500);
            } else {
                $("#"+divID).css(
                {
                    'left': numMinimized*200,
                    'margin': '2px',
                    'width': '196px',
                    'height': 'auto',
                    'top': '0px',
                    'padding': '3px',
                });

            }
            $("#"+divID+"-minimized-wrapper").css('display', 'block');
            $("#"+divID+"-maximized-wrapper").css('display', 'none');
            numMinimized += 1;
        };

        /*
            Maximizes the file list.
            @param divID The root ID of the object to maximize.
        */
        var maximizeObject = function(divID){
            function resetDims(){
                $("#"+divID).css('width', 'auto');
                $("#"+divID).css('height', 'auto');
            }
            $("#"+divID).animate(previousSizes[divID], 
            {
                duration: 500,
                complete: resetDims 
            });
            $("#"+divID+"-maximized-wrapper").css('display', 'block');
            $("#"+divID+"-minimized-wrapper").css('display', 'none');
            numMinimized -= 1;
        };

        /*
            Function to be called on resizing. Not leaving this anonymous so that it can be called at the beginning without triggering the Diva .resize() listener.
        */
        var resizeComponents = function()
        {
            topbarHeight = $("#topbar").height();
            $("#topbar").css({
                'left': '0.2%',
                'width': '99.6%' 
            });
            $("#container").css({
                'top': topbarHeight,
                'left': '0.2%',
                'width': '99.6%',
                'height': window.height - topbarHeight,
            });
            containerWidth = $("#container").width();
            innerMargin = containerWidth * 0.006; //for inner margin
            windowHeight = $(window).height() - topbarHeight - 7; //7 for padding
            $("#mei-editor").height(windowHeight);
            $("#diva-wrapper").height(windowHeight);
            $("#editor").height(windowHeight);
            $("#editor").width((containerWidth / 2) - innerMargin);
            $("#diva-wrapper").width((containerWidth / 2) - innerMargin);
        }

        /*
            Function ran on initialization.
        */
        var _init = function()
        {
            /*                +'<div id="file-upload">' //the file upload 
                +'<div id="file-upload-maximized-wrapper">' //what shows when it's maximized
                +'<input type="file" value="Add a new file" id="fileInput">' 
                +'<div id="file-list">Files loaded:<br></div>'
                +'<button id="updateDiva">Update DIVA</button>'
                +'<button class="minimize" name="file-upload" style="float:right;">Minimize</button>'
                +'</div>'
                +'<div id="file-upload-minimized-wrapper" style="display:none;">' //or when it's minimized
                +'<span id="file-list">Files loaded:</span>'
                +'<button class="maximize" name="file-upload" style="float:right;">Maximize</button>'
                +'</div>'
                +'</div>'*/
            element.height($(window).height());
            element.append('<div id="topbar">'
                +'</div>' //header
                +'<div id="container">'
                +'<div id="editor"></div>' //ACE editor
                +'<div id="diva-wrapper"></div>' //Diva
                +'<div class="clear"></div>'
                +'<span id="hover-div"></span>' //the div that pops up when highlights are hovered over
                +'</div>' //container for body
                );
            pluginLength = plugins.length;
            while(pluginLength--){
                curPlugin = plugins[pluginLength];
                $("#topbar").append('<div id="'+curPlugin.divName+'" class="toolbar-object">'
                    +'<div id="'+curPlugin.divName+'-maximized-wrapper">'
                    +curPlugin.maximizedAppearance
                    +'</div>'
                    +'<div id="'+curPlugin.divName+'-minimized-wrapper" style="display:none;">'
                    +curPlugin.minimizedAppearance
                    +'</div>'
                    +'</div>'
                    );
                minimizeObject(curPlugin.divName, true);
                $("#"+curPlugin.divName).draggable();
                console.log()
                curPlugin._init(self, settings);
            }
            //create the diva wrapper and editor
            $('#diva-wrapper').diva(
            {
                contained: true,
                enableAutoHeight: true,
                enableAutoWidth: true,
                fixedHeightGrid: false,
                iipServerURL: "http://132.206.14.136:8000/fcgi-bin/iipsrv.fcgi",
                objectData: "imagesOut.json",
                imageDir: "/opt/stgall",
                enableHighlight: true,
                viewerWidthPadding: 0,
                viewerHeightPadding: 0,
            });
            settings.dv = $('#diva-wrapper').data('diva');

            settings.editor = ace.edit("editor"); //create the ACE editor
            settings.editor.setTheme("ace/theme/ambiance");
            settings.editor.getSession().setMode("ace/mode/xml");

            //various jQuery listeners that have to be put in after the buttons exist
            $(".minimize").on('click', function(event)
            {
                minimizeObject(event.target.name);
            });
            $(".maximize").on('click', function()
            {
                maximizeObject(event.target.name);
            });

            //Events.subscribe("VisiblePageDidChange") - have ACE page automatically update to reflect currently viewed page?

            //load in the XML validator

            $.ajax(
            {
                url: settings.validatorLink,
                success: function(data)
                {
                    settings.validatorText = data;
                }
            });

            //little graphics things
            $(window).on('resize', resizeComponents);

            resizeComponents();
        };

        _init();

    }

    $.fn.AceMeiEditor = function (plugins, options)
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
            var meiEditor = new AceMeiEditor(this, plugins, options);
            element.data('AceMeiEditor', meiEditor);
        });
    };

})(jQuery);