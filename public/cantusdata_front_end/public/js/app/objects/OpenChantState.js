define(['underscore', 'marionette'],
    function (_, Marionette) {

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
                    console.error('Invalid manuscript/folio ids for chant state; need strings but got:', manuscript, folio);
                    return;
                }

                // Create the manuscript if it doesn't exist
                this.ensureCreated(manuscript);

                var prevChant = this.manuscripts[manuscript][folio];

                // Normalize undefined chants to null
                if (chantNumber === void 0)
                    chantNumber = null;

                if (chantNumber !== prevChant)
                {
                    this.manuscripts[manuscript][folio] = chantNumber;
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
                // TODO(wabain): hook up localStorage
            },

            /**
             * Ensure that a registry exists for a manuscript
             *
             * @param {string} manuscript the manuscript id
             * @returns {boolean} true if created, false if already exists
             */
            ensureCreated: function(manuscript)
            {
                // If the key doesn't exist, then add it
                if (!(manuscript in this.manuscripts))
                {
                    // TODO(wabain): check localStorage here

                    // Create a new folio set
                    this.manuscripts[manuscript] = {};
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