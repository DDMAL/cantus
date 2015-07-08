define(['underscore', 'marionette'],
    function (_, Marionette)
    {
        "use strict";

        return Marionette.Object.extend({
            initialize: function ()
            {
                this.manuscripts = {};
            },

            /**
             * Set which chant is open for some particular manuscript folio.
             *
             * @param {string} manuscript the id of the manuscript
             * @param {string} folio the name of the folio
             * @param {?number} chantNumber the open chant
             */
            set: function(manuscript, folio, chantNumber)
            {
                if (!(_.isString(manuscript) && _.isString(folio)))
                {
                    // jshint devel:true
                    console.error('Invalid manuscript/folio ids for chant state; need strings but got:',
                        manuscript, folio);
                    return;
                }

                // Create the manuscript if it doesn't exist
                this.ensureCreated(manuscript);

                var prevChant = this.manuscripts[manuscript][folio];

                // Normalize undefined chants to null
                if (prevChant === void 0)
                    prevChant = null;

                if (chantNumber === void 0)
                    chantNumber = null;

                if (chantNumber !== prevChant)
                {
                    // If the chant has been removed, delete it from the manuscript
                    if (chantNumber === null)
                    {
                        delete this.manuscripts[manuscript][folio];
                    }
                    else
                    {
                        this.manuscripts[manuscript][folio] = chantNumber;
                    }

                    this.persist(manuscript);
                }
            },

            /**
             * Get which chant is open for a particular manuscript folio
             *
             * @param {string} manuscript manuscript id
             * @param {string} folio folio code
             * @returns {?number}
             */
            get: function(manuscript, folio)
            {
                var folios = this.manuscripts[manuscript];

                if (!folios)
                    return null;

                var chant = folios[folio];

                return chant === void 0 ? null : chant;
            },

            /**
             * Save the chant state for the manuscript persistently on the client side
             *
             * @param {string} manuscript the manuscript id
             */
            persist: function (manuscript)
            {
                if (window.localStorage)
                {
                    var key = this.getLocalStorageKey(manuscript);
                    var data = JSON.stringify(this.manuscripts[manuscript]);

                    try
                    {
                        window.localStorage.setItem(key, data);
                    }
                    catch (e)
                    {
                        // jshint devel:true
                        console.error('Failed to save open chants to local storage:\n', e);
                    }
                }
            },

            /**
             * Ensure that a registry exists for a manuscript
             *
             * @param {string} manuscript the manuscript id
             * @returns {boolean} true if created, false if already exists
             */
            ensureCreated: function(manuscript)
            {
                if (manuscript in this.manuscripts)
                {
                    return false;
                }

                // Try to load the data from localStorage
                if (window.localStorage)
                {
                    var key = this.getLocalStorageKey(manuscript);
                    var data;

                    try
                    {
                        data = window.localStorage.getItem(key);
                    }
                    catch (e)
                    {
                        // jshint devel:true
                        console.error('Failed to load open chants for manuscript', manuscript,
                            'from local storage:\n', e);
                    }

                    if (data)
                    {
                        try
                        {
                            this.manuscripts[manuscript] = JSON.parse(data);
                            return true;
                        }
                        catch (e)
                        {
                            // jshint devel:true
                            console.error('Failed to read open chant data for manuscript', manuscript, ':\n', e);
                        }
                    }
                }

                // Otherwise, create a new folio set
                this.manuscripts[manuscript] = {};

                // It has been created, so return true
                return true;
            },

            getLocalStorageKey: function(manuscript)
            {
                return 'openChants:' + manuscript;
            }
        });
    });