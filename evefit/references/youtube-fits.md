# Fits from EVE YouTube videos

EVE YouTubers publish working fits in video descriptions, in pinned comments and
comment threads, and sometimes only on screen inside the fitting window. Use
them as a baseline after the fit libraries, before inventing a fit.

Source order inside one video:

1. description and chapters;
2. comments (pinned and high-liked first, then replies);
3. video frames only when neither contains a usable text fit.

Always record the video URL and the timestamp where the fit appears.

## Find a video

Search the web or YouTube for `EVE Online <hull> <activity> fit`,
`<hull> solo pvp fit 2026` or `EVE Online abyssal <hull>`. Well-known fitting
channels include Suitonia, Bjorn Bee, Chessur and Delonewolf; treat this as a
starting point and check that the channel actually covers the hull and activity.
Prefer recent videos: module stats and meta change with balance patches.

If the user names a video, use it directly. If several plausible videos exist
and the request does not say which one matters, pick the most recent fit that
matches hull and activity and say which video you used.

## Commands

```bash
python3 scripts/evefit.py youtube info URL --comments 40
python3 scripts/evefit.py youtube fits URL --comments 80 --out ./yt-fits
python3 scripts/evefit.py youtube frames URL --out ./yt-frames --scene 0.25 --max 18
python3 scripts/evefit.py youtube frames URL --out ./yt-frames --at 12:34 --at 18:02
python3 scripts/evefit.py youtube frames ./local-video.mp4 --out ./yt-frames --interval 20
python3 scripts/evefit.py youtube ocr ./yt-frames/frame_000123.jpg
```

`info` prints title, channel, chapters, description/comment sizes and how many
text fits were found. `fits` prints every EFT-shaped block with its origin
(`description`, `comment by NAME`) and timestamp; `--out DIR` saves each
candidate as a `.eft` file. Metadata is cached under
`~/.cache/evefit/youtube/<video-id>.json`; `--refresh` refetches it.

`frames` downloads at most 480p (`--height`), then extracts frames by scene
change (default threshold 0.25), by fixed interval, or at exact timestamps and
writes labelled 3x3 contact sheets. Sheets keep the image count small. Use
`--at` when the description, comments or chapters point at the moment the fit
is shown; that is the fastest and most precise path.

`--cookies FILE` passes a Netscape cookie file for age or region restricted
videos. `--from-json FILE` reads saved metadata without touching the network,
which also lets you reuse a JSON another tool produced.

## Reading a fit off the screen

1. Start with the contact sheet. It labels each tile with a frame number and
   timestamp. Find the tile that shows the EVE fitting window with the ship
   name, module list and rigs visible.
2. Re-extract only those moments at higher detail:
   `youtube frames URL --out DIR --at MM:SS` (add `--height 720`).
3. Read the fitting window row by row. EVE shows low slots, medium slots, high
   slots and rigs in separate columns; drones appear under the ship or in the
   drone bay panel. Module tooltips give exact meta level when the icon text is
   too small.
4. If the fitting window is split across shots (podcasts often scroll it),
   collect one frame per section and merge the module lists.
5. Transcribe English names as printed. Then run `checknames` and fix every
   unknown name with the suggestions or `search`.
6. Run `validate`. An on-screen fit is evidence of intent, not proof: patch
   changes, missing implants, or a misread meta level can make it invalid.

Never transcribe from a thumbnail. Thumbnails are staged art. Do not trust
overlay text added by an editor either; use the in-game fitting window.

## Choosing among candidates

- Prefer a fit that states its purpose and environment in the video or comment.
- Prefer a fit with the hull, role and activity matching the request; a PvP
  brawler shown in a nullsec roam is not an Abyssal runner.
- Prefer the newest listed fit when several work; note the video date.
- If a comment corrects the description fit, treat the correction as a
  variant and validate both.
- If the video only shows a fit for a different purpose than the request, keep
  looking before adapting it.

## Limits

- Age-restricted, members-only and region-blocked videos may need `--cookies`.
- YouTube blocks some networks (SSL errors, `UNEXPECTED_EOF_WHILE_READING`).
  When that happens, say so and fall back to the fit libraries or to a JSON the
  user supplies; do not invent a description of the video.
- OCR is optional: it needs the `tesseract` binary plus `pytesseract` and
  `pillow`. Without it, read the contact sheet and higher-resolution frames
  directly.
- Frame inspection costs images. Keep to one or two sheets per video and do not
  re-view frames you already inspected; extract new timestamps instead.
