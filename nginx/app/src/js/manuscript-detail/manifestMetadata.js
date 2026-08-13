/**
 * Pick a display string out of a IIIF v3 language map ({ en: ["..."], ... }),
 * preferring English and otherwise the first language present. Multiple values
 * are joined with <br> since the attribution is rendered as HTML.
 */
function pickLanguageValue(languageMap) {
    if (!languageMap)
        return undefined;

    var language = languageMap.en ? 'en' : Object.keys(languageMap)[0];
    var values = languageMap[language];
    return Array.isArray(values) ? values.join('<br>') : values;
}

/**
 * Flatten a IIIF manifest's image-rights fields into the shape the manuscript
 * info sidenav renders: { imageAttribution, imageLogoUrl, imageLicence }.
 *
 * Cantus serves both IIIF Presentation API v2 and v3 manifests, so each field
 * tries the v3 location first and falls back to the v2 one.
 */
export default function extractImageAttribution(manifest) {
    var provider = manifest.provider && manifest.provider[0];
    var providerLogo = provider && provider.logo && provider.logo[0];

    var v2Logo = manifest.logo;
    if (v2Logo && typeof v2Logo === 'object')
        v2Logo = v2Logo['@id'];

    return {
        imageAttribution: manifest.requiredStatement
            ? pickLanguageValue(manifest.requiredStatement.value)
            : manifest.attribution,
        imageLogoUrl: providerLogo ? providerLogo.id : v2Logo,
        imageLicence: manifest.rights || manifest.license
    };
}
