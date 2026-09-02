# colincahill.dev

Personal site. One static HTML file, no framework, no build step, no dependencies
beyond three Google Fonts.

## What's in it

`index.html` is the whole site: markup, stylesheet, and the JavaScript port of the
Pathfinder scoring engine. Everything runs client side, so the demo works with the
page opened straight off disk.

`build_profile.py` regenerates the scoring profile inside `index.html` from
Pathfinder's `profile.yaml`. It is a development tool and is not served to
visitors.

The scoring engine mirrors `pathfinder_scoring.py` in
[cpcahill/Pathfinder](https://github.com/cpcahill/Pathfinder): the same hard
filters, the same seven weighted axes, the same weights.

## Keeping the site and the app in agreement

The `PROFILE` object in `index.html` is **generated**, not hand-written. It sits
between `BEGIN GENERATED` and `END GENERATED` markers and is produced from
Pathfinder's `profile.yaml`, which stays the only place any of this is defined.

```bash
python3 build_profile.py                    # assumes ../ProjectPathfinder
python3 build_profile.py path/to/profile.yaml
python3 build_profile.py --check            # exits 1 if index.html is stale
```

Run it after any change to `profile.yaml`. The `--check` form writes nothing and
is suitable for a pre-commit hook or a CI step.

This exists because the first version of the port was copied by hand and had
already drifted before the site was published: 86 skill aliases against the app's
123, and 27 cities against 41. A job in a city the site had never heard of scored
lower there than in the app, while the page claimed the two matched.

### Verifying parity

The five sample postings in the `SAMPLES` array are also worth running through
the Python engine when you change scoring logic on either side. Build the same
`Job` objects in `pathfinder_scoring.py` and compare. At the time of writing both
engines return 98, 94, 66, rejected, and 22 for the five samples.

### One deliberate difference

The Python app detects contract roles from Adzuna's `contract_type` field. A
static page has no API to read, so it infers from the posting text instead, using
a deliberately narrow pattern (`contract to hire`, `contract role`, `6 month
contract`, and similar) rather than any occurrence of the word. A permanent role
that happens to mention contracts will not be penalised, but an unusually worded
contract posting may slip through. That is the only place the two engines can
legitimately disagree.

## Running it locally

Open `index.html` in a browser. That's it. To serve it over HTTP instead:

```bash
python3 -m http.server 8000
```

## Deploying to GitHub Pages

1. Create a repository. Naming it `cpcahill.github.io` publishes at that domain
   with no further configuration; any other name publishes under
   `cpcahill.github.io/<repo-name>/`.
2. Push this folder to the `main` branch.
3. In the repository, go to **Settings → Pages**, set **Source** to
   "Deploy from a branch", branch `main`, folder `/ (root)`, and save.
4. Wait a minute or two for the first build.

### Using a custom domain

1. Buy the domain (Namecheap, Cloudflare, Porkbun are all fine, roughly $12/year).
2. Add a file named `CNAME` in this folder containing only the domain, no protocol:
   ```
   colincahill.dev
   ```
3. At the registrar, create four `A` records for the apex domain pointing at
   GitHub's Pages IPs, and a `CNAME` record for `www` pointing at
   `cpcahill.github.io`. GitHub's current IPs are listed in their Pages docs;
   check them there rather than trusting a copy in this file.
4. In **Settings → Pages**, enter the domain and tick **Enforce HTTPS** once the
   certificate has been issued.

## Editing

The content is plain HTML in reading order: hero, work, engine, stack, contact.

- Colours and type are CSS custom properties in the `:root` block at the top.
  Light values are the base; the dark palette is redefined twice, once for
  `prefers-color-scheme` and once for the explicit `[data-theme="dark"]` stamp
  that the theme button sets. Change a colour in all three places or the themes
  drift apart.
- Claims carry evidence tags (`measured`, `projected`, `self-reported`) via a
  `<span class="tag ...">`. If you add a number to the page, tag it. That
  convention is the point of the design, and an untagged figure reads as an
  oversight.
- Sample postings for the demo live in the `SAMPLES` array near the bottom of the
  script. The `senior` entry exists to demonstrate a hard-filter rejection; keep
  one like it if you swap the samples out.

## Not included, on purpose

No analytics, no cookie banner, no tracking. If you add analytics later, say so
on the page.
