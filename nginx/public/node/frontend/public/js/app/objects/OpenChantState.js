import _ from 'underscore';
import Marionette from 'marionette';

/**
 * NOTE: The OpenChantState object stores the state of chants
 * for a particular manuscript in sessionStorage. Chant states
 * are reset in new sessions (eg. new tabs or upon navigating
 * away from the detail view of a particular manuscript). While 
 * this has been implemented as a default so that chant do not
 * "remain open" across visits some time apart, a future feature
 * could allow users to decide whether or not chant states should
 * reset or persist across multiple sessions and windows (ie. whether
 * sessionStorage or localStorage should be used). When this feature
 * is implemented logic in the various methods of this object ("persist",
 * "ensureCreated") should be added to read and write chant states
 * to sessionStorage or localStorage based on user preferences, rather
 * than to sessionStorage only.
 */


export default Marionette.Object.extend({
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
        if (_.isArray(folio)){
            folio = folio.join(",");
        }

        if (!(_.isString(manuscript) && _.isString(folio)))
        {
            /* eslint-disable no-console */
            console.error('Invalid manuscript/folio ids for chant state; need strings but got:',
                manuscript, folio);
            /* eslint-enable no-console */

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
        if (window.sessionStorage) 
        {
            var key = this.getSessionStorageKey(manuscript);
            var data = JSON.stringify(this.manuscripts[manuscript]);

            try
            {
                window.sessionStorage.setItem(key, data);
            }
            catch (e)
            {
                /* eslint-disable no-console */
                console.error('Failed to save open chants to local storage:\n', e);
                /* eslint-enable no-console */
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

        // Try to load the data from sessionStorage
        if (window.sessionStorage)
        {
            var key = this.getSessionStorageKey(manuscript);
            var data;

            try
            {
                data = window.sessionStorage.getItem(key);
            }
            catch (e)
            {
                /* eslint-disable no-console */
                console.error('Failed to load open chants for manuscript', manuscript,
                    'from local storage:\n', e);
                /* eslint-enable no-console */
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
                    /* eslint-disable no-console */
                    console.error('Failed to read open chant data for manuscript', manuscript, ':\n', e);
                    /* eslint-enable no-console */
                }
            }
        }

        // Otherwise, create a new folio set
        this.manuscripts[manuscript] = {};

        // It has been created, so return true
        return true;
    },

    getSessionStorageKey: function(manuscript)
    {
        return 'openChants:' + manuscript;
    }
});
