# Acquisition scope and citation limits

graver retains dated, structured observations from Find a Grave. It does not make
an archival copy of a memorial page and does not turn a website statement into an
accepted genealogical fact. This guide explains what the acquisition levels mean,
what the current record can support, and what researchers must preserve elsewhere.

## What the acquisition levels mean

`summary` means graver observed a memorial in Find a Grave search results. The
retained observation can contain:

- memorial ID and memorial URL;
- displayed name components, nickname, and maiden name;
- displayed birth and death text;
- famous and veteran indicators;
- memorial type;
- cemetery ID, displayed burial place, and plot; and
- the observation time, outcome, and graver parser version.

`full` means graver requested and observed the individual memorial page, then
retained the supported structured fields. It contains the summary categories plus:

- displayed original name;
- displayed birth and death places;
- displayed coordinates;
- whether a biography section was detected, but not its text;
- displayed date added; and
- Find a Grave-displayed relationship links, including their displayed group,
  memorial ID, URL, name, life/date text, and marriage year when available.

The current memorial row is a convenient latest representation. Immutable summary
and full observations retain the dated payloads that produced it. A later summary
does not erase full-only fields or replace earlier observations.

## What `full` does not mean

`full` does not mean complete, exhaustive, verified, or accepted. graver 1.0.0rc1
does not retain:

- the memorial page's HTML or a visual snapshot;
- biography text;
- photographs, captions, credits, or image attribution;
- contributor, manager, sponsorship, or edit-history details;
- every label, panel, link, or other element displayed on the page;
- the content of linked memorial pages; or
- the civil, cemetery, newspaper, image, or other underlying records that may
  support statements on the memorial.

Observing a relationship link does not retrieve the linked page and does not prove
the displayed relationship. `has_bio: true` records only that graver detected a
biography section. It does not preserve, quote, or evaluate the biography.

## Four different kinds of missing information

Use these distinctions in notes and citations:

- **Not displayed:** the examined representation affirmatively showed that an
  element was absent. graver's current structured observation usually cannot prove
  this for page elements outside its supported fields.
- **Not collected:** the page may have displayed the element, but graver did not
  extract it. Contributor details are an example in this release.
- **Not retained:** graver used or observed content transiently but did not store
  it. The page HTML and biography text are examples.
- **Not examined:** graver did not request or inspect the representation. Linked
  memorial pages, images, and underlying records are examples unless the researcher
  examines them separately.

A null or missing structured value must not automatically be described as “not
displayed.” It may reflect source absence, non-collection, a changed page, or a
parser limitation. Record the narrower claim that the retained observation does not
contain the value unless direct examination of the dated representation establishes
why. A later visit to a mutable live page cannot prove what an earlier snapshot did
or did not display. Do not use a null structured field as negative evidence.

## Citation boundary

A retained acquisition provides useful citation ingredients: the website and
memorial URL, memorial ID, displayed person and cemetery information, observation
date, acquisition level, and graver version. A conservative citation draft can use
this pattern, adapted to the citation style required by the research project:

> Find a Grave, memorial page for “[displayed name]” ([displayed lifespan]),
> memorial [ID], [displayed cemetery and locality], [URL] (observed [date]); graver
> structured [summary/full] observation. Selected fields retained; not a complete
> page archive.

Include “and images,” contributor attribution, biography quotations, or an
underlying record only when the researcher actually examined and separately cited
that material. The retained observation cannot establish that an uncollected
element was absent from the live page.

For professional work, continue recording as applicable:

- the research question and search scope;
- a citation appropriate to the representation actually examined;
- contributor, image, caption, and attribution details;
- permitted copies, screenshots, or complete transcriptions of material relied on;
- exact biography text used in analysis;
- source classification, informant assessment, and information quality;
- conflicts, correlations, negative searches, and researcher-authored conclusions;
  and
- whether missing material was absent, uncollected, unretained, or unexamined.

graver's observation is a provenance foundation, not a substitute for a research
log, source analysis, or proof argument. Where family history keeps its receipts,
the receipt still needs to say what was—and was not—in the bag.
