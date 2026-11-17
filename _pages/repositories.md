---
layout: page
permalink: /repositories/
title: repos
description: Todo mi código y material público en GitHub.
nav: true
nav_order: 4
---
{% assign own = site.data.repos.repos | where: "fork", false %}
{% assign forks = site.data.repos.repos | where: "fork", true %}
<h2 class="repo-section-title">Repositorios ({{ own.size }})</h2>
<div class="repo-grid">
{% for repo in own %}
<a class="repo-card" href="{{ repo.url }}" target="_blank" rel="noopener">
<span class="repo-card-name"><i class="fa-brands fa-github"></i><span>{{ repo.name }}</span></span>
{% if repo.description != "" %}<span class="repo-card-desc">{{ repo.description }}</span>{% endif %}
<span class="repo-card-meta">{% if repo.language != "" %}<span class="repo-card-lang">{{ repo.language }}</span>{% endif %}<span class="repo-card-stars"><i class="fa-solid fa-star"></i> {{ repo.stars }}</span></span>
</a>
{% endfor %}
</div>
<h2 class="repo-section-title">Forks ({{ forks.size }})</h2>
<div class="repo-grid">
{% for repo in forks %}
<a class="repo-card" href="{{ repo.url }}" target="_blank" rel="noopener">
<span class="repo-card-name"><i class="fa-solid fa-code-fork"></i><span>{{ repo.name }}</span></span>
{% if repo.description != "" %}<span class="repo-card-desc">{{ repo.description }}</span>{% endif %}
<span class="repo-card-meta">{% if repo.language != "" %}<span class="repo-card-lang">{{ repo.language }}</span>{% endif %}<span class="repo-card-stars"><i class="fa-solid fa-star"></i> {{ repo.stars }}</span></span>
</a>
{% endfor %}
</div>
