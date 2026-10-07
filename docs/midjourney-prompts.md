# APT illustration prompts for Midjourney

One house style for every image, so the site reads like a single magazine. Paste the **style block** after each scene. Keep the same `--sref` image once you have a result you like, so every apartment looks drawn by the same hand.

## Style block (append to every prompt)

```
mid-century magazine cover illustration, flat gouache on cold-press paper, confident black ink outlines with a slight hand wobble, limited palette of muted sky blue, ochre, brick red, sage green and warm cream, visible paper grain, gentle wit, no text, no lettering, no logos --ar 20:13 --style raw --stylize 150
```

For a consistent series: generate the hero image first, pick the best one, then add `--sref <that image URL>` to every other prompt.

## Hero (homepage)

```
a single bright one-bedroom apartment seen from the doorway, three tall windows with a small city skyline beyond, late-afternoon sun laying yellow stripes across a wood floor, a green sofa with a black cat asleep on it, a round red side table with one coffee cup, a potted plant by the window, everything tidy and calm
```

## The No engine (one per card)

```
a renter standing in an empty apartment holding a long paper receipt that unrolls across the floor and out the door, small amused expression
```

```
a pleasant bedroom at night, a single bed by the window, outside the window a wide road full of headlights and a bus, the sleeper holding a pillow over their head
```

```
a handsome apartment on the ground floor, a passerby's legs and a dog visible through the window at eye level, dim interior, a houseplant leaning toward the little light there is
```

## Listings

| Apartment | Scene (put before the style block) |
|---|---|
| Larkspur House 604 | sixth-floor apartment with floor-to-ceiling south windows, quiet courtyard trees below, green sofa, black cat in a sun stripe |
| Ninebark Flats 3B | corner apartment in a 1920s brick walk-up, windows on two walls, morning sun from both sides, radiator under the window, rust-colored sofa |
| Fieldstone Lofts 211 | converted schoolhouse loft, enormous old multi-pane windows, timber floor, navy sofa, a chalkboard-green wall, generous open space |
| Juniper & Third 2F | calm apartment facing a park, treetops filling the windows, soft north light, olive sofa, a person reading with headphones off |
| Langdon Terrace 5A | modern apartment overlooking a lake at golden hour, sailboats in the window, tan sofa, two calendar pages floating away marked free |
| Thimbleberry Commons 402 | apartment above a busy neighborhood street, bakery and café awnings visible below, morning bustle, sage sofa, bicycle by the door |
| Orchard Row House 2 | apartment in a 1904 house, big bay window, built-in bookshelves, high ceilings, worn rug, an older stove glimpsed through a doorway |
| Bassett Yard 701 | seventh-floor apartment with a west glass wall, city rooftops and a distant train, a price tag on a string drifting downward outside the window |
| Hartwell Commons 12C | high-rise apartment, tall windows partly shaded by the building next door, elegant but slightly dim, purple-grey sofa |
| Belvedere House PH2 | top-floor penthouse in a restored 1930s limestone building, skylight and windows on three sides, flooded with light, teal sofa, a small terrace |

## Using the images on the site

1. Export each image at 1600 × 1040 or larger, saved as WebP.
2. Name them by apartment id: `larkspur.webp`, `ninebark.webp`, `fieldstone.webp`, and so on, plus `hero.webp`.
3. Put them in an `img/` folder next to `index.html`.
4. Ask Claude to switch the drawn illustrations for these files. The illustration caption on each apartment stays, so no one mistakes them for listing photos.

Check Midjourney's current terms for commercial use on your plan before publishing.
