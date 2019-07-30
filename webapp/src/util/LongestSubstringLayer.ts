import * as _ from 'lodash';

// regexPlateLayers is responsible for converting layers to plates, so that
// repeated patterns of layers are reduced down to plates, as seen in
// graphical models.  It differs from plateLayers in that it uses a simple
// regular expression to match repetitions.
export function regexPlateLayers(layersData, compactLayersData) {
    // Greedily finds the first repeat of layers.  Can be improved to recurse
    // greedily, or to find all repeats and score them, then recurse.

    // We need to add some logic for skip connections here.  For now, we filter out
    // the unique ID of the layer.  Eventually, we need to figure out if the skips are
    // within the plate or without of the plate.  If they are within the plate, need to
    // make a new string for "skip length", and if they are outside the plate, we
    // leave them in as attributes.  But then there are self loops...  That does complicate
    // things.
    const layerStrings: string[] = compactLayersData
        .map((attrs) => attrs.filter((a) => a.title !== 'id' && a.title !== 'skipTo')
                                .map((a) => `${a.title}|${a.value}`).join('|||'));

    const matches = layerStrings.join('').match(/(type.+)\1+/);
    if (matches && matches[1]) {
        const maxSubstring = matches[1].split((/(?=type)/g));
        // then, we loop through the original layers, and mark the start, end, and skip layers
        let matchIndex = 0;
        let layerIndex = 0;
        let hasMatched = false;
        let startIndex = 0;
        let numMatches = 0;
        for (const layerString of layerStrings) {
            if (layerString === maxSubstring[matchIndex]) {
                matchIndex += 1;
                if (matchIndex === maxSubstring.length) {
                    if (hasMatched) {
                        // we mark all layers as skipped
                        for (let i = 0; i < maxSubstring.length; i++) {
                            layersData[layerIndex - i].plateSkipped = true;
                        }
                    } else {
                        // we mark the start and end layers and reset the match index
                        startIndex = layerIndex - maxSubstring.length + 1;
                        layersData[layerIndex - maxSubstring.length + 1].plateStart = true;
                        layersData[layerIndex].plateEnd = true;
                        for (let i = 0; i < maxSubstring.length; i++) {
                            layersData[layerIndex - i].inPlate = true;
                        }
                        hasMatched = true;
                    }
                    numMatches += 1;
                    matchIndex = 0;
                }
            }
            layerIndex += 1;
        }
        // We add the number of repetitions of the plate.
        layersData[startIndex].numPlates = numMatches;
    }
    return layersData;
}
