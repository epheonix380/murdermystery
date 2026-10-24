# Hollowpine Lodge case hub

A static site for "The Last Chapter at Hollowpine Lodge". It has two files, `index.html` and `data.js`, and no build step.

## Put it on GitHub Pages

1. Create a new public repository on GitHub, for example `hollowpine`.
2. Upload `index.html`, `data.js` and this README (Add file → Upload files), then commit.
3. Go to Settings → Pages. Under "Build and deployment", pick **Deploy from a branch**, branch `main`, folder `/ (root)`, and save.
4. After a minute your hub is live at `https://<your-username>.github.io/hollowpine/`.

## Codes

| Code | Opens |
| --- | --- |
| WOLF | Marcus Reed (the killer) |
| BREW | Vivian Thorne |
| FANG | Julian Thorne |
| KEYS | Ruth Kowalski |
| ROT | Graham Pike (optional) |
| ORB | Madame Oriel (optional) |
| BOO | Penny Lark (optional) |
| RAVEN | GM page |
| STORM | Round 2 code, typed on the Body tab |

Players enter their code on the **Me** tab. The GM page has the solution, puzzle answers, the reveal script and the buttons to print clue cards and labels.

## Notes

- Progress (Round 2, solved puzzles, the code you opened) is saved per phone in that browser. "Reset this device" on the GM page clears it.
- The 3D body loads three.js from jsDelivr, so the site needs internet. If it can't load, the hotspot buttons under the viewer still show every clue.
- To change any text, edit `data.js`.
- Nothing is secret from someone who reads the source. That's fine for a party.
