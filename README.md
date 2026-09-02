# cpcahill.github.io

My personal site. One HTML file, no framework and no build step.

**Live:** https://cpcahill.github.io

## What's here

```
index.html          The whole site: markup, styles, and scripts
build_profile.py    Updates the demo's scoring data from Pathfinder
```

The site has a working demo of the scoring engine from my
[Pathfinder](https://github.com/cpcahill/Pathfinder) project, rewritten in
JavaScript so it runs in the browser. You can pick a sample job posting or
paste in a real one and watch it get scored. Nothing is sent anywhere.

## Running it locally

Open `index.html` in a browser. That is the whole setup.

To serve it over HTTP instead:

```bash
python3 -m http.server 8000
```

## Updating the demo

The scoring data in `index.html` is generated from Pathfinder's
`profile.yaml`, so the site and the app always agree on how a job is scored.
After changing `profile.yaml`, run:

```bash
python3 build_profile.py
```

It looks for `../ProjectPathfinder/profile.yaml` by default. You can also
pass a path, or use `--check` to see whether the site is out of date without
changing anything.

Do not edit the block between `BEGIN GENERATED` and `END GENERATED` in
`index.html` by hand. That script overwrites it.

## Deploying

The site is hosted on GitHub Pages and updates automatically on every push to
`main`.

## Built with

Plain HTML, CSS, and JavaScript. Fonts are Archivo, Newsreader, and IBM Plex
Mono from Google Fonts.
