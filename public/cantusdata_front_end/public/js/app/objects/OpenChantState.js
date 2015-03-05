define(['marionette'],
    function (Marionette) {

        "use strict";

        return Marionette.Object.extend
        ({
            manuscripts: {},

            /**
             * Set which chant is open for some particular manuscript folio.
             *
             * @param manuscript
             * @param folio
             * @param chantNumber
             */
            setOpenChant: function(manuscript, folio, chantNumber)
            {
                // Create the manuscript if it doesn't exist
                this.createManuscript(manuscript);

                this.manuscripts[String(manuscript)][String(folio)] = parseInt(chantNumber);
            },

            /**
             * Get which chant is open for a particular manuscript folio
             *
             * @param manuscript siglum_slug
             * @param folio folio code
             * @returns {*}
             */
            getOpenChant: function(manuscript, folio)
            {
                var manuscriptString = String(manuscript);
                var folioString = String(folio);

                // Return the number if it is open
                if (manuscriptString in this.manuscripts && folioString in this.manuscripts[manuscriptString])
                {
                    // A chant number has been stored, so lets return it
                    return this.manuscripts[manuscriptString][folioString];
                }
                else
                {
                    // No chant number has been stored
                    return undefined;
                }
            },

            /**
             * Add a manuscript to the OpenChantState.
             *
             * @param manuscript siglum_slug
             * @returns {boolean} true if created, false if already exists
             */
            createManuscript: function(manuscript)
            {
                // Make sure the manuscript is a string for our key
                var manuscriptString = String(manuscript);
                // If the key doesn't exist, then add it
                if (!(manuscriptString in this.manuscripts))
                {
                    // Create a new folio set
                    this.manuscripts[manuscriptString] = {};
                    // It has been created, so return true
                    return true;
                }
                else
                {
                    // It already exists!
                    return false;
                }
            }
        });
    });