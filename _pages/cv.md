---
layout: page
permalink: /cv/
title: cv
nav: true
nav_order: 2
description: Formación, docencia e investigación.
---
{% assign cv = site.data.cv.cv %}
<div class="cv-page">
<div class="cv-downloads">
<a class="cv-download-btn" href="{{ '/assets/pdf/Matias_Zabaljauregui_CV.pdf' | relative_url }}" target="_blank" rel="noopener"><i class="fa-solid fa-file-pdf"></i> CV completo (PDF, en inglés)</a>
</div>
<section class="cv-section">
<h2 class="cv-section-title">Resumen</h2>
<p class="cv-summary">{{ cv.summary }}</p>
</section>
<section class="cv-section">
<h2 class="cv-section-title">Docencia e investigación</h2>
{% for e in cv.sections.Experience %}
{% assign sy = e.start_date | append: "" | slice: 0, 4 %}
{% assign ey = e.end_date | append: "" %}
{% if ey == "present" %}{% assign ey = "actualidad" %}{% else %}{% assign ey = ey | slice: 0, 4 %}{% endif %}
<div class="cv-entry">
<div class="cv-entry-year">{{ sy }}{% if sy != ey %} – {{ ey }}{% endif %}</div>
<div class="cv-entry-body">
<div class="cv-entry-title">{{ e.position }}</div>
<div class="cv-entry-institution">{{ e.company }}{% if e.location %} · {{ e.location }}{% endif %}</div>
{% if e.summary %}<div class="cv-entry-desc">{{ e.summary }}</div>{% endif %}
</div>
</div>
{% endfor %}
</section>
<section class="cv-section">
<h2 class="cv-section-title">Formación</h2>
{% for e in cv.sections.Education %}
{% assign sy = e.start_date | append: "" | slice: 0, 4 %}
{% assign ey = e.end_date | append: "" %}
{% if ey == "present" %}{% assign ey = "actualidad" %}{% else %}{% assign ey = ey | slice: 0, 4 %}{% endif %}
<div class="cv-entry">
<div class="cv-entry-year">{{ sy }}{% if sy != ey %} – {{ ey }}{% endif %}</div>
<div class="cv-entry-body">
<div class="cv-entry-title">{{ e.studyType }} en {{ e.area }}</div>
<div class="cv-entry-institution">{{ e.institution }}{% if e.location %} · {{ e.location }}{% endif %}</div>
{% for h in e.highlights %}<div class="cv-entry-desc">{{ h }}</div>{% endfor %}
</div>
</div>
{% endfor %}
</section>
<section class="cv-section">
<h2 class="cv-section-title">Publicaciones</h2>
{% for e in cv.sections.Publications %}
<div class="cv-entry">
<div class="cv-entry-year">{{ e.releaseDate | append: "" | slice: 0, 4 }}</div>
<div class="cv-entry-body">
<div class="cv-entry-title">{{ e.title }}</div>
<div class="cv-entry-institution">{{ e.authors | join: ", " }}</div>
<div class="cv-entry-desc">{{ e.publisher }}. {{ e.summary }}</div>
</div>
</div>
{% endfor %}
</section>
<section class="cv-section">
<h2 class="cv-section-title">Habilidades</h2>
{% for s in cv.sections.Skills %}
<div class="cv-skill">
<div class="cv-skill-label">{{ s.name }}</div>
<div class="cv-skill-tags">{{ s.keywords }}</div>
</div>
{% endfor %}
</section>
</div>
