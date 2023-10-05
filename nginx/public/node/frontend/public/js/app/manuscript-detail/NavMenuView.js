import Marionette from "marionette";
import Backbone from "backbone";
import $ from 'jquery';

import navitemtemplate from "./nav-item.template.html";

var manuscriptChannel = Backbone.Radio.channel('manuscript');

var NavItemModel = Backbone.Model.extend({});

var NavMenuCollection = Backbone.Collection.extend({
    model: NavItemModel
});

var folioNavOptions = [
    {navTitle:"Folio 2r", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9435874", 
    navDescription: "The Annunciation"},
    {navTitle:"Folio 33r", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9435938", 
    navDescription: "The Nativity"},
    {navTitle:"after Folio 45v", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9435965", 
    navDescription: "The Adoration of the Magi"},
    { navTitle: "after Folio 50v", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9435976", 
    navDescription: "The Baptism of Christ"},
    { navTitle: "after Folio 117v", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9436113", 
    navDescription: "The Agony in the Garden of Gethsemane"},
    { navTitle: "after Folio 124v", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9436128", 
    navDescription: "The Resurrection"},
    { navTitle: "after Folio 124v", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9436129", 
    navDescription: "The Assembly of the Saints"},
    { navTitle: "after Folio 133v",
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9436145", 
    navDescription: "Holy Kinship"},
    { navTitle: "Folio A24v", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9436323", 
    navDescription: "Saint Maurice"},
    { navTitle: "Folio A30r", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9436334", 
    navDescription: "Saint Hubert"},
    { navTitle: "Folio A36v", 
    imageLink:"https://lib.is/IE9434868/iiif/2/FL9436345", 
    navDescription: "Saint Juliana"}
    ]


const NavItemView =  Marionette.ItemView.extend({
        template: navitemtemplate,
        ui :{
            highlightCard: '.highlight-card'
        },
        events: {
            'click @ui.highlightCard': '_goToImage'
        },
        _goToImage: function(){
            manuscriptChannel.request('set:imageURI', this.model.get('imageLink'), {replaceState:true});
            $('#salzinnesNavMenuModal').modal('hide');
        }
    });

const NavMenuView = Marionette.CollectionView.extend({
    childView: NavItemView,
    tagName: 'div',
    className: 'highlight-collection',
    id: 'salzinnes-highlight-folios'
});

const testNavMenuCollection = new NavMenuCollection();
testNavMenuCollection.set(folioNavOptions);


export {NavMenuView, testNavMenuCollection}