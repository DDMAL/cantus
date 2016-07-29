import _ from "underscore";
import ManuscriptItemBaseView from "./ManuscriptItemBaseView";

export default ManuscriptItemBaseView.extend({
    serializeData: function ()
    {
        var data = _.pick(this.model.attributes, 'name', 'url', 'date', 'folio_count', 'chant_count');

        // jscs:disable requireCamelCaseOrUpperCaseIdentifiers

        return _.extend(data, {
            short_name: this.model.get('provenance') + ', ' + this.model.get('siglum'),
            primary_url_is_external: false,
            cantus_url: this.model.get('cantus_url')
        });

        // jscs:enable
    }
});
